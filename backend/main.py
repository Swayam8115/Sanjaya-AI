import asyncio
from app.agents.master_agent import run_master_agent


async def main():
    print("\nMaster Agent")
    user_query = input("\nEnter your query: ")

    print("\nProcessing...\n")
    result = await run_master_agent(user_query)

    print("Final Output\n")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

# show me sales and clinical trials of Metformin
