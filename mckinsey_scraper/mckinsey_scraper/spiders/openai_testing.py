import json
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv(dotenv_path="../../../.env")

# Set the OpenAI API key
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Define the word count limit as a macro
WORD_COUNT_LIMIT = 50  # You can adjust this as needed


def summarize_content(article_text):
    try:
        # Prepare the prompt for summarization
        prompt = (
            f"Summarize the following content in {WORD_COUNT_LIMIT} words or fewer, you will only return summary, do not include extra information:\n\n"
            f"{article_text}"
        )

        # Call the OpenAI API
        chat_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=WORD_COUNT_LIMIT,
            temperature=0.7,
            service_tier="default",
            stream=False,
        )

        print(chat_completion)

        # Extract the summary from the response
        summary = chat_completion.choices[0].message.content.strip()
        return summary

    except Exception as e:
        print(f"Failed to generate summary: {e}")
        return "Failed to generate summary."


def main():
    # Load the JSON file
    input_file = "sample_input.json"  # Replace with your JSON file path
    output_file = "sample_output_with_summaries.json"  # Output file path

    items = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line.strip())  # Parse each line as a JSON object
                items.append(item)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")

    # Process each item in the JSON file
    for item in items:
        if isinstance(item, dict):  # Ensure the item is a dictionary
            article_text = item.get("article_text", "")
            if article_text:
                summary = summarize_content(article_text)
                item["summary"] = summary
                print(f"Summary: {summary}\n")
        else:
            print(
                "Unexpected item format in JSON file. Each item should be a dictionary."
            )

    # Save the results to a new JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        # drop the article_text key
        for item in items:
            item.pop("article_text", None)
        json.dump(items, f, indent=4)

    print(f"Summaries saved to {output_file}")


if __name__ == "__main__":
    main()
