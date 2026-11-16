total_in = (len(PROMPT)*len(new)+new["text"].str.len().sum())/3
tokens_in = round(total_in)
tokens_out = 20 * len(new)
cost = round(tokens_in / 1000 * 0.3 + tokens_out / 1000 * 1.5, 1)
share_prompt = round(len(PROMPT) * len(new) / 3 / total_in, 3)
print(tokens_in, tokens_out, cost, share_prompt)