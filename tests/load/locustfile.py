from locust import HttpUser, task, between, events
import random
import time
import logging

logger = logging.getLogger(__name__)

CONFIG = {
    "voice_path": "../audio/reference.wav",
    "voice_exaggeration": 0.5,
    "wait_time_min": 1,
    "wait_time_max": 3,
    "fail_ratio_warning": 0.05,
}

SAMPLE_TEXTS = [
    "Hello, this is Chatterbox Turbo speaking.",
    "The quick brown fox jumps over the lazy dog.",
    "Text-to-speech technology has advanced significantly in recent years.",
    "Machine learning models can generate realistic human-like voices.",
    "This is a test of emergency broadcast system.",
    "Welcome to the future of voice synthesis.",
    "Chatterbox Turbo delivers high-quality speech generation.",
    "Optimizing performance requires careful measurement and analysis.",
    "Concurrent requests can reveal bottlenecks in the system.",
    "GPU utilization is crucial for real-time inference.",
]


class TTSLoadTest(HttpUser):
    wait_time = between(CONFIG["wait_time_min"], CONFIG["wait_time_max"])

    def on_start(self):
        self.voice_loaded = False
        self.load_voice()

    @task(3)
    def generate_speech(self):
        if not self.voice_loaded:
            self.load_voice()

        text = random.choice(SAMPLE_TEXTS)

        with self.client.post(
            "/generate",
            json={"text": text},
            catch_response=True,
            name="/generate",
            stream=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                if "no_voice_loaded" in response.text:
                    self.voice_loaded = False
                    self.load_voice()
                    response.failure("No voice loaded, reloading...")
                else:
                    response.failure(response.text)
            else:
                response.failure(response.text)

    def load_voice(self):
        try:
            response = self.client.post(
                "/load_voice",
                json={
                    "voice_path": CONFIG["voice_path"],
                    "exaggeration": CONFIG["voice_exaggeration"],
                },
                name="/load_voice",
            )
            if response.status_code == 200:
                self.voice_loaded = True
                logger.info("Voice loaded successfully")
            else:
                logger.error(f"Failed to load voice: {response.text}")
        except Exception as e:
            logger.error(f"Error loading voice: {e}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("Starting load test...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("Load test completed.")
    if environment.stats.total.fail_ratio > CONFIG["fail_ratio_warning"]:
        logger.warning(f"High failure ratio: {environment.stats.total.fail_ratio:.2%}")
