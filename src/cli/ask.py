import argparse

from src.agent.chain import FileSearchAgent

# HOWEVER you load chunks in your project
# This MUST be the same source used for indexing
def load_chunks():
    """
    Replace this with your real chunk-loading logic.
    For now, this assumes chunks were saved or cached somewhere.
    """
    # Example placeholder
    # return [{"text": "...", "meta": {"source": "file.txt"}}]
    raise NotImplementedError("Implement chunk loading here")


def main():
    parser = argparse.ArgumentParser(
        description="Ask questions over your indexed documents"
    )
    parser.add_argument(
        "question",
        type=str,
        help="Question to ask the document store"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to retrieve"
    )

    args = parser.parse_args()

    chunks = load_chunks()
    agent = FileSearchAgent(chunks)

    answer = agent.ask(args.question)
    print("\n=== ANSWER ===\n")
    print(answer)


if __name__ == "__main__":
    main()
