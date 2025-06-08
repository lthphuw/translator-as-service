import asyncio
import httpx
import time

# from application.main.config import settings

API_URL = "http://localhost:8080/api/v0/translate/"
NUM_REQUESTS = 20
TGT_LANG = "vi"

SAMPLE_SENTENCES = [
    "Hello, how are you?",
    "What time is it?",
    "Can you help me with this task?",
    "Where is the nearest restaurant?",
    "I love learning new languages.",
    "This translation service is very fast.",
    "Artificial intelligence is evolving rapidly.",
    "The weather is nice today.",
    "Do you speak French or Vietnamese?",
    "Let’s go to the beach this weekend.",
    "She is preparing dinner now.",
    "Please take a seat and wait.",
    "I’m reading a great book about history.",
    "My dog loves to play fetch.",
    "He works as a software engineer.",
    "We need to buy some groceries.",
    "They are traveling to Japan next month.",
    "This is a challenging problem to solve.",
    "Can you translate this sentence?",
    "Good morning! Have a nice day.",
]


async def send_request(client, i, text):
    try:
        response = await client.post(
            API_URL,
            json={"texts": [text], "tgt_lang": TGT_LANG},
            timeout=10.0,
        )
        print(
            f"[{i}] Status: {response.status_code}, Time: {response.elapsed.total_seconds():.2f}s"
        )
        if response.status_code != 200:
            print(f"   Detail: {response.json()}")
    except Exception as e:
        print(f"[{i}] Exception: {e}")


async def main():
    async with httpx.AsyncClient() as client:
        tasks = [
            send_request(client, i, text)
            for i, text in enumerate(SAMPLE_SENTENCES[:NUM_REQUESTS])
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    print(f"Total duration: {time.time() - start:.2f}s")
