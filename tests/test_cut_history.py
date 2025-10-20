from promoai.prompting.prompt_engineering import cut_conversation

def test_cut_history():
    conversation = [
        {"role": "user", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "user", "content": "Please update the model to fix it based on the provided feedback."},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "Can you tell me a joke?"},
        {"role": "assistant", "content": "Why did the scarecrow win an award? Because he was outstanding in his field!"},
        {"role": "user", "content": "That's funny! Tell me another one."},
        {"role": "user", "content": "Please update the model to fix it based on the provided feedback."}
    ]
    index = 6
    cut_conv = cut_conversation(conversation, index)
    assert cut_conv[-1]["content"] == "That's funny! Tell me another one."
    index = -1
    # We expect an exception
    try:
        cut_conv = cut_conversation(conversation, index)
        assert False, "Expected an exception for negative index"
    except ValueError:
        pass
    index = 10
    # We expect an exception
    try:
        cut_conv = cut_conversation(conversation, index)
        assert False, "Expected an exception for out-of-bounds index"
    except ValueError:
        pass
    index = 4
    cut_conv = cut_conversation(conversation, index)
    assert cut_conv[-1]["content"] == "Can you tell me a joke?"
    index = 3
    cut_conv = cut_conversation(conversation, index)
    assert cut_conv[-1]["content"] == "Hello!"
