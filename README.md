# BGPq Proxy

A simple REST API that serves as a proxy to bgpq3/bgpq4.

## Requirements

This project relies on Python with Flask and Redis as caching database.

## Calling The API

The current implementation exposes two different endpoints:

* one to get the prefixes based on an ASN
* one to get the prefixes based on an AS-SET

Both endpoints answer to `GET` requests and will give IPv4 and IPv6 prefix
lists back. They also accept two optional parameters:

* `?invalidate=1` will make the API forgot about the cached result and will
  avoid caching the new result
* `?no_cache=1` will forbid the API to look for the result in the cache and
  cache the new result

### ASN Endpoint

Query: `GET /bgpq/asn/201281`

Response:

```json
{
    "ipv4": [
        {
            "prefix": "45.154.62.0/24",
            "exact": true
        }
    ],
    "ipv6": [
        {
            "prefix": "2001:678:794::/48",
            "exact": true
        },
        {
            "prefix": "2a0f:b100:200::/40",
            "exact": true
        }
    ]
}
```

### AS-SET Endpoint

Query: `GET /bgpq/as-set/AS-MAZOYER-EU`

Response:

```json
{
    "ipv4": [
        {
            "prefix": "45.154.62.0/24",
            "exact": true
        }
    ],
    "ipv6": [
        {
            "prefix": "2001:678:794::/48",
            "exact": true
        },
        {
            "prefix": "2a0f:b100:200::/40",
            "exact": true
        }
    ]
}
```

A specific optional parameter to limit the depth while resolving the AS-SET
prefix list can be passed. Use `?depth=<value>` where value is a positive
interger, `0` meaning no depth limit.