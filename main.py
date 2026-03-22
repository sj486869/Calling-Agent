import asyncio
import traceback
import os
import logging

from dotenv import load_dotenv
from videosdk.agents import (
    Agent,
    AgentSession,
    RealTimePipeline,
    JobContext,
    RoomOptions,
    WorkerJob,
    Options,
)
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig

logging.basicConfig(level=logging.INFO)
load_dotenv()

# Patch for vsaiortc/VideoSDK audio bug where CustomAudioStreamTrack.recv() can return None
# causing RTCRtpSender to call encoder.pack(None) and crash with "'NoneType' object has no attribute 'pts'".
try:
    from videosdk.agents.room.audio_stream import (
        CustomAudioStreamTrack,
        MixingCustomAudioStreamTrack,
        MediaStreamError,
    )

    async def _safe_recv(self):
        frame = await _original_recv(self)
        if frame is None:
            # Signal no further stream
            raise MediaStreamError("Audio stream ended")
        return frame

    if not hasattr(CustomAudioStreamTrack, "_recv_monkeypatched"):
        _original_recv = CustomAudioStreamTrack.recv
        CustomAudioStreamTrack.recv = _safe_recv
        CustomAudioStreamTrack._recv_monkeypatched = True

    if not hasattr(MixingCustomAudioStreamTrack, "_recv_monkeypatched"):
        _original_mixing_recv = MixingCustomAudioStreamTrack.recv

        async def _safe_mixing_recv(self):
            frame = await _original_mixing_recv(self)
            if frame is None:
                raise MediaStreamError("Audio stream ended")
            return frame

        MixingCustomAudioStreamTrack.recv = _safe_mixing_recv
        MixingCustomAudioStreamTrack._recv_monkeypatched = True
except Exception:
    logging.exception("Failed to apply audio track recv patch")

# Patch websocket settings for Gemini Live handshake/keepalive reliability
try:
    import videosdk.plugins.google.live_api as vs_live_api

    # Check if ws_connect exists before patching
    if hasattr(vs_live_api, 'ws_connect'):
        _original_ws_connect = vs_live_api.ws_connect

        def _ws_connect_with_retry(uri, *args, **kwargs):
            kwargs.setdefault("ping_interval", 30)
            kwargs.setdefault("ping_timeout", 60)
            kwargs.setdefault("close_timeout", 30)
            kwargs.setdefault("max_size", 2 ** 20)
            kwargs.setdefault("max_queue", None)
            return _original_ws_connect(uri, *args, **kwargs)

        vs_live_api.ws_connect = _ws_connect_with_retry
    else:
        logging.warning("ws_connect not found in live_api, skipping websocket patch")
except Exception:
    logging.exception("Failed to patch ws_connect keepalive settings")

# Patch AUDIO_STREAM_ENABLED event to guard against None data
try:
    from videosdk.agents.event_bus import global_event_emitter

    _original_emit = global_event_emitter.emit

    def _safe_emit(event, *args):
        if event == "AUDIO_STREAM_ENABLED" and (not args or args[0] is None):
            _original_emit(event, {})
            return
        _original_emit(event, *args)

    global_event_emitter.emit = _safe_emit
except Exception:
    logging.exception("Failed to patch audio stream event emitter")


# Define the agent's behavior and personality
class MyVoiceAgent(Agent):
    """
    A voice agent that handles phone calls with helpful and friendly responses.
    """

    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful AI assistant that answers phone calls. "
                "Keep your responses concise and friendly. "
                "Always listen carefully to the caller and provide accurate information. "
                "If you don't know something, admit it politely and offer to help in other ways."
            ),
        )

    async def on_enter(self) -> None:
        """Called when the agent enters the conversation."""
        await self.session.say(
            "Hello! I'm your real-time assistant. How can I help you today?"
        )

    async def on_exit(self) -> None:
        """Called when the agent exits the conversation."""
        await self.session.say("Goodbye! It was great talking with you!")


async def start_session(context: JobContext) -> None:
    """
    Starts the agent session with retry logic for connection.
    """
    # Validate environment variables
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    auth_token = os.getenv("VIDEOSDK_AUTH_TOKEN")
    if not auth_token:
        raise ValueError("VIDEOSDK_AUTH_TOKEN environment variable is not set")

    session = None
    try:
        # Configure the Gemini model for real-time voice
        model = GeminiRealtime(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            api_key=api_key,
            config=GeminiLiveConfig(
                voice="Leda",
                response_modalities=["AUDIO"],
            ),
        )

        pipeline = RealTimePipeline(model=model)
        session = AgentSession(agent=MyVoiceAgent(), pipeline=pipeline)

        connect_attempts = 0
        max_connect_attempts = 8
        backoff = 2

        while connect_attempts < max_connect_attempts:
            try:
                await context.connect()
                await session.start()
                logging.info("Agent session connected and started")
                break
            except Exception as exc:
                connect_attempts += 1
                logging.error(
                    f"start_session attempt {connect_attempts}/{max_connect_attempts} failed: {exc}"
                )
                if connect_attempts >= max_connect_attempts:
                    raise
                await asyncio.sleep(backoff)
                backoff = min(30, backoff * 2)

        await asyncio.Event().wait()

    finally:
        if session is not None:
            try:
                await session.close()
            except Exception:
                logging.exception("Error closing session")

        try:
            await context.shutdown()
        except Exception:
            logging.exception("Error shutting down context")


def make_context() -> JobContext:
    """
    Creates the job context with optimized room options.
    """
    room_options = RoomOptions(
        no_participant_timeout_seconds=120,
        auto_end_session=False,
        background_audio=True,
    )
    return JobContext(room_options=room_options)


if __name__ == "__main__":
    try:
        # Validate required environment variables
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY environment variable must be set")
        if not os.getenv("VIDEOSDK_AUTH_TOKEN"):
            raise ValueError("VIDEOSDK_AUTH_TOKEN environment variable must be set")

        # Register the agent with a unique ID
        options = Options(
            agent_id="MyTelephonyAgent",  # CRITICAL: Unique identifier for routing
            register=True,                # REQUIRED: Register with VideoSDK for telephony
            max_processes=10,             # Concurrent calls to handle
            host="localhost",             # Local debug server host
            port=0,                       # Auto-assign free port
        )

        job = WorkerJob(
            entrypoint=start_session,
            jobctx=make_context,
            options=options,
        )
        logging.info("Starting VideoSDK agent worker...")
        job.start()

    except Exception as e:
        logging.error(f"Failed to start agent: {e}")
        traceback.print_exc()
