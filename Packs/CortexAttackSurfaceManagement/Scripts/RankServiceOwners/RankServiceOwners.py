import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
"""Script for identifying and recommending the most likely owners of a discovered service
from those surfaced by Cortex ASM Enrichment.
"""


from typing import Dict, List, Any
import traceback
from itertools import groupby


def score(owners: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Owner score is the number of observations on that owner divided by the max number of observations
    for any owner in the list

    Expects `count` key and replaces it with `ranking score`
    """
    if owners:
        max_count = max(owner.get('count', 1) for owner in owners)
        for owner in owners:
            count = owner.pop('count', 1)
            owner['ranking score'] = count / max_count
    return owners


def rank(owners: List[Dict[str, Any]], k: int = 5) -> List[Dict[str, Any]]:
    """
    Return up to k owners with the highest ranking scores
    """
    if k <= 0:
        raise ValueError(f'Number of owners k={k} must be greater than zero')
    return sorted(owners, key=lambda x: x['ranking score'])[:k]


def justify(owners: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    For now, `justification` is the same as `source`; in the future, will sophisticate
    """
    for owner in owners:
        owner['justification'] = owner.get('source', '')
    return owners


def _canonicalize(owner: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canonicalizes an owner dictionary and adds a deduplication key
    `canonicalization` whose value is either:
        1. whitespace-stripped and lower-cased email, if email exists
        2. whitespace-stripped and lower-cased name
        3. empty string if neither exists
    """
    if owner.get('email', ''):
        owner['canonicalization'] = owner['email'].strip().lower()
        owner['email'] = owner['canonicalization']
    elif owner.get('name', ''):
        owner['canonicalization'] = owner['name'].strip().lower()
        owner['name'] = owner['canonicalization']
    else:
        owner['canonicalization'] = ''
    return owner


def canonicalize(owners: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Calls _canonicalize on each well-formatted owner; drops and logs malformated inputs
    """
    canonicalized = []
    try:
        for owner in owners:
            try:
                canonicalized.append(_canonicalize(owner))
            except Exception as e:
                demisto.error(f"Unable to canonicalize {owner}: {e}")
    except Exception as e:
        demisto.error(f"`owners` must be iterable: {e}")
    return canonicalized


def aggregate(owners: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Aggregate owners by their canonicalization.

    If canonicalized form is email, preserve longest name.
    Preserve max timestamp and union over sources.

    Aggregate remaining keys by type: union over strings, and max over numerical types.
    If type is neither of the above, all values of that key will be dropped from the aggregated owner.
    """
    deduped = []
    sorted_owners = sorted(owners, key=lambda owner: owner['canonicalization'])
    for key, group in groupby(sorted_owners, key=lambda owner: owner['canonicalization']):
        duplicates = list(group)
        email = duplicates[0].get('email', '')
        # the if condition in the list comprehension below defends against owners whose Name value is None (not sortable)
        names = sorted(
            [owner.get('name', '') for owner in duplicates if owner.get('name')],
            key=lambda x: len(x), reverse=True
        )
        name = names[0] if names else ''
        # aggregate Source by union
        source = ' | '.join(sorted(
            set(owner.get('source', '') for owner in duplicates if owner.get('source', ''))
        ))
        # take max Timestamp if there's at least one; else empty string
        timestamps = sorted(
            [owner.get('timestamp', '') for owner in duplicates if owner.get('timestamp', '')], reverse=True
        )
        timestamp = timestamps[0] if timestamps else ''
        owner = {
            'name': name,
            'email': email,
            'source': source,
            'timestamp': timestamp,
            'count': len(duplicates)
        }

        # aggregate remaining keys according to type
        all_keys = set(k for owner in duplicates for k in owner.keys())
        keys_to_types = {k: type(owner[k]) for owner in duplicates for k in owner.keys()}
        other_keys = all_keys - {'name', 'email', 'source', 'timestamp', 'canonicalization'}
        for other in other_keys:
            if keys_to_types[other] == str:
                # union over strings
                owner[other] = ' | ' .join(sorted(
                    set(owner.get(other, '') for owner in duplicates if owner.get(other, ''))
                ))
            elif keys_to_types[other] in (int, float):
                # max over numerical types
                owner[other] = max(owner.get(other, 0) for owner in duplicates)
            else:
                demisto.info(f'Cannot aggregate owner detail {other} -- removing from service owner')
                continue
        deduped.append(owner)
    return deduped


def main():
    try:
        owners = demisto.args().get("owners", [])
        top_k = justify(rank(score(aggregate(canonicalize(owners)))))
        demisto.executeCommand("setAlert", {"asmserviceowner": top_k})
        return_results(CommandResults(readable_output='top 5 service owners written to asmserviceowner'))

    except Exception as ex:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute IdentifyServiceOwners. Error: {str(ex)}')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
