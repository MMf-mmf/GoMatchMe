# from openai import OpenAI
# import json

# # set the api key in the environment variable
# os.environ["OPENAI_API_KEY"] = "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"
# client = OpenAI(
#     # This is the default and can be omitted
#     api_key=os.environ.get("OPENAI_API_KEY"),
# )

# suggestion = Suggestion.objects.first()
# suggestion_data = {
#     "message": suggestion.message,
#     "email": suggestion.email,
#     "phone_number": suggestion.phone_number,
#     "boys_first_name": suggestion.boys_first_name,
#     "boys_last_name": suggestion.boys_last_name,
#     "boys_mothers_name": suggestion.boys_mothers_name,
#     "boys_fathers_name": suggestion.boys_fathers_name,
#     "boys_age": suggestion.boys_age,
#     "boys_country": suggestion.boys_country,
#     "boys_city": suggestion.boys_city,
#     "girls_first_name": suggestion.girls_first_name,
#     "girls_last_name": suggestion.girls_last_name,
#     "girls_mothers_name": suggestion.girls_mothers_name,
#     "girls_fathers_name": suggestion.girls_fathers_name,
#     "girls_age": suggestion.girls_age,
#     "girls_country": suggestion.girls_country,
#     "girls_city": suggestion.girls_city,
#     "girls_sect": list(suggestion.girls_sect),
#     "boys_sect": list(suggestion.boys_sect),
# }


# def check_spam(suggestion_data):
#     prompt = f"""
#     Analyze the following suggestion data to determine if it's spam, valid, or has an invalid message. The input is a suggestion for two singles to meet, proposed to a matchmaker. Pay special attention to the 'message' field.

#     Return a JSON object with these 4 fields and nothing else!:
#     1. "spam_result": string ("spam", "valid")
#     2. "spam_confidence": float (between 0 and 1)
#     3. "message_quality": string ("good" or "bad")
#     4. "message_confidence": float (between 0 and 1)

#     Suggestion data:

#     {suggestion_data}

#     Analysis criteria:
#     1. Message quality:
#     - If the "message" is short or nonsensical, mark it as "bad"
#     - A good "message" should explain why the match is suitable and provide meaningful context

#     2. Other data fields:
#     - Check for completeness and validity of all required fields
#     - Look for any suspicious patterns or inconsistencies

#     3. Overall assessment:
#     - If the "message" is good but other data looks suspicious, lean towards "spam"
#     - If all data looks valid including a good "message", return "valid"


#     Provide your determination based on these criteria, emphasizing the importance of the "message" quality.
#     """

#     # Make the API call
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant that analyzes data for spam."},
#             {"role": "user", "content": prompt},
#         ],
#     )

#     # Parse the response
#     # result = json.loads(response.choices[0].message.content)
#     # return result
#     return [response.choices[0].message.content, response]


# # Example usage
# suggestion_data = {
#     # "message": "test suggesion not real",
#     # "message": "they would make good lovers",
#     "message": "I think these two would be a great match because they both love to read and enjoy long walks on the beach.",
#     "email": "allin2ship@gmail.com",
#     "phone_number": "1234567890",
#     "boys_first_name": "Yossi",
#     "boys_last_name": "Weinstein",
#     "boys_mothers_name": "Chana Levine",
#     "boys_fathers_name": "Shmuel Weinstein",
#     "boys_age": 25,
#     "boys_country": "CA",
#     "boys_city": "Jerusalem",
#     "girls_first_name": "Rivka",
#     "girls_last_name": "Greenberg",
#     "girls_mothers_name": "Malka Rubinstein",
#     "girls_fathers_name": "Shneur Greenberg",
#     "girls_age": 32,
#     "girls_country": "GB",
#     "girls_city": "GB",
#     "girls_sect": ["Chassidish"],
#     "boys_sect": ["Yeshivish"],
# }

# result = check_spam(suggestion_data)

# print(result[0])
# # print(result[1])


# def interpret_spam_check(result):
#     try:
#         # Parse the JSON string into a Python dictionary
#         spam_check = json.loads(result[0].strip().lstrip("```json").rstrip("```").strip())

#         if spam_check["spam_result"] == "spam":
#             if spam_check["message_quality"] == "good":
#                 return "This suggestion looks like spam, even though the message quality is good. There might be issues with other data fields."
#             else:
#                 return "This suggestion is likely spam. The message quality is poor and there may be other issues with the data."
#         else:
#             if spam_check["message_quality"] == "good":
#                 return "This suggestion appears to be valid. The message quality is good and the data seems legitimate."
#             else:
#                 return (
#                     "This suggestion might be valid, but the message quality is poor. Consider improving the message."
#                 )
#     except json.JSONDecodeError:
#         return "Error: Unable to parse the spam check result. Please ensure the result is in valid JSON format."
#     except KeyError as e:
#         return f"Error: Missing expected key in the spam check result: {str(e)}"


# # Example usage
# spam_check_result = result  # Assuming this is the JSON string from your previous code
# interpretation = interpret_spam_check(spam_check_result)
# print(interpretation)
