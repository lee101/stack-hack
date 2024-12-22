from prompt_gemini import gemini_generation, analyze_site, get_similar_domain_names

def test_gemini_generation():
    # Test basic generation
    input_text = "Hello, how are you?"
    response = gemini_generation(input_text)
    assert isinstance(response, str)
    assert len(response) > 0

    # Test with history
    history = [
        {"role": "user", "parts": ["Hi"]},
        {"role": "model", "parts": ["Hello!"]}
    ]
    response = gemini_generation(input_text, history)
    assert isinstance(response, str)
    assert len(response) > 0

def test_analyze_site(tmp_path):
    
    # Create test HTML file
    test_domain = "midjourney.com"
        
    # Test analysis
    result = analyze_site(test_domain)
    print(result)
    assert isinstance(result, str)
    assert len(result) > 0
    # Test cached result
    cached_result = analyze_site(test_domain)
    assert cached_result == result


def test_get_similar_domain_names():
    domain = "midjourney.com"
    result = get_similar_domain_names(domain)
    print(result)
    assert isinstance(result, list)
    assert len(result) > 0
