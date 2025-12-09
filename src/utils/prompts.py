USER_PROMPTS = [
    "Check the weather in London for the next 3 days. If any day has rain, find indoor activities and save them to rainy_activities.txt. If all days are sunny, search for outdoor parks and save to sunny_activities.txt. Also send me an email summarizing the plan.",
    "Search for news about Tesla stock. If the stock went up, calculate how much $10,000 invested last month would be worth now and email me the result. If it went down, search for analyst opinions and summarize them for me instead.",
    "I'm traveling to Paris next Monday for 3 days. Check the weather forecast, find the currency exchange rate from USD to EUR for $500, search for popular tourist attractions, translate them in Italian and create a summary document called paris_trip.txt with all this information",
    "Read all .txt files in the documents folder, analyze the sentiment of each, create a comparison report showing which documents are most positive vs negative, and email the report to manager@company.com",
    "You're given multilingual customer reviews. Build a workflow to clean, translate, embed each review, and cluster them conceptually using only the tools available.",
    "Given a text input, classify it using predefined labels. But if classification confidence is low, apply additional preprocessing (cleaning → translation → re-classification).",
    "You're given numerical training data. Compute descriptive statistics, train a regression model, and generate predictions. If the variance of the output variable is under a threshold, switch to a simpler model.",
    "Generate a user profile from a long biography text. If the profile extraction fails or the text is too short, ask for web search results about that person and retry."
]