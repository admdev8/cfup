cfup - CloudFlare Updater
=========================

cfup.py is a simple script to update CloudFlare DNS entries.

Sample Configuration
--------------------

    {
        "user": "test@example.com",
        "api_key": "abcd01234567890abcd01234567890abcd012",
        "zones": {
            "test.example.com": [
                {
                    "record_id": "99408286",
                    "info": "mailcontrol.logon-server.com"
                }
            ],
            "example.com": [
                {
                    "record_id": "26420695",
                    "info": "example.com"
                },
                {
                    "record_id": "110485660",
                    "info": "git.example.com"
                },
                {
                    "record_id": "110488972",
                    "info": "store.example.com"
                },
                {
                    "record_id": "118495309",
                    "info": "dnsupdate.example.com"
                }
            ]
        },
        "dyndns": {
        	"test2.example.com": "118567687"
        }
    }


