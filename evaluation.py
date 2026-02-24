import json
from utils.matcher import match_internships

def evaluate_top_k(k=5):

    with open("evaluation_data.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)

    correct = 0
    total = len(test_data)

    i = 0
    while i < total:

        resume = test_data[i]["resume_text"]
        expected = test_data[i]["expected_title"]

        results = match_internships(resume, top_n=k)

        found = False
        j = 0
        while j < len(results):
            if results[j]["title"] == expected:
                found = True
                break
            j += 1

        if found:
            correct += 1

        i += 1

    accuracy = correct / total

    print(f"Top-{k} Accuracy: {round(accuracy * 100, 2)}%")

if __name__ == "__main__":
    evaluate_top_k(5)