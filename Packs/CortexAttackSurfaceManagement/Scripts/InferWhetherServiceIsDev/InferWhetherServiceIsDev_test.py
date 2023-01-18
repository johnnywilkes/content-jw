import demistomock as demisto  # noqa: F401


def test_canonicalize():
    """
    Tests canonicalize() helper function.
    
    Given:
        - (nothing)
    When:
        - Running the canonicalize method on a string
    Then:
        - Checks that extra characters are stripped and result is lowercase
    """
    from InferWhetherServiceIsDev import _canonicalize_string
    assert _canonicalize_string("BLAH") == "blah"
    assert _canonicalize_string("'BLAH'") == "blah"
    assert _canonicalize_string('" BLAH" ') == "blah"


def test_is_dev_according_to_key_value_pairs():
    """
    Tests the "is dev" assessor for key-value pair data.
    
    Given:
        - (nothing)
    When:
        - Running the is_dev_according_to_key_value_pairs method on key-value data
    Then:
        - Checks that we get True when there are indicators of non-production,
        as long as they aren't also accompanied by a conflicting indicator of
        being prod
    """
    from InferWhetherServiceIsDev import is_dev_according_to_key_value_pairs

    # dev indicator with varying keys
    assert is_dev_according_to_key_value_pairs([{"Key": "env", "Value": "dev"},
                                                {"Key": "Name", "Value": "rdp_server"},
                                                {"Key": "test", "Value": ""}])
    assert is_dev_according_to_key_value_pairs([{"Key": "ENVIRONMENT", "Value": "TEST"}])

    # pre-prod counts as dev and not as prod
    assert is_dev_according_to_key_value_pairs([{"Key": "Stage", "Value": "status - preprod"}])

    # no dev indicator
    assert not is_dev_according_to_key_value_pairs([{"Key": "env", "Value": "prod"}])
    assert not is_dev_according_to_key_value_pairs([{"Key": "dev", "Value": "my name"}])

    # conflicting indicators
    assert not is_dev_according_to_key_value_pairs([{"Key": "env", "Value": "prod"},
                                                    {"Key": "env", "Value": "dev"}])

    # extra arguments ok
    assert is_dev_according_to_key_value_pairs([{"Key": "ENVIRONMENT", "Source": "AWS", "Value": "TEST"}])


def test_is_dev_according_to_classifications():
    """
    Tests the "is dev" assessor for Xpanse classification data.
    
    Given:
        - (nothing)
    When:
        - Running the is_dev_according_to_classifications method on a list
        of strings
    Then:
        - Checks that we get True when the input list contains the DevelopmentEnvironment
        classification
    """
    from InferWhetherServiceIsDev import is_dev_according_to_classifications

    assert is_dev_according_to_classifications(["SshServer", "DevelopmentEnvironment"])
    assert not is_dev_according_to_classifications(["RdpServer", "SelfSignedCertificate"])
