import asyncio
import time

async def brew_coffee():
    print("Brewing coffee...")
    await asyncio.sleep(3)  # Simulate time taken to brew coffee
    print("End brewing coffee!")
    return "Coffee is ready!"

async def toast_bagels():
    print("Toasting bagels...")
    await asyncio.sleep(2)  # Simulate time taken to toast bagels
    print("End toasting bagels!")
    return "Bagels are toasted!"


async def main():
    start_time = time.time()

    # batch processing using asyncio.gather
    # batch = asyncio.gather(
    #     brew_coffee(),
    #     toast_bagels()
    # )
    # result_coffee, result_bagels = await batch

    coffee_task = asyncio.create_task(brew_coffee())
    bagels_task = asyncio.create_task(toast_bagels())
    result_coffee = await coffee_task
    result_bagels = await bagels_task

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Result of brewing coffee: {result_coffee}")
    print(f"Result of toasting bagels: {result_bagels}")
    print(f"Total time taken: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())