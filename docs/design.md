# Design

The purpose of this document is to clearly identify:

* Project goals
* Project requirements to meet those goals
* Project specifications to meet those requirements

## Goals

1. Provide a place where /r/The_Donald users can congregate, meme, and otherwise interact, in the event that reddit admins choose to ban /r/The_Donald

## Requirements

### General

1. To the greatest extent possible, mimic reddit functionality as it applies to /r/the_donald (Quarantine/ban status notwithstnading)
2. Use reddit oauth to validate new users and import usernames from reddit to new accounts, allowing for continuous preservation of identity and username recognition
3. No advertising, donations only (to avoid contractual obligations to advertisers)

### UX

1. Allow submission of links and text
2. Allow commenting on submissions
3. Allow commenting on comments
4. Allow up/down voting on submissions and comments
5. Sort submissions by new, hot, etc
6. Allow users to delete their own content
7. Allow users to report submissions and comments

### Administration

Several layers of administrative privilege will be implemented

Integer|Name|Suggested permissions|Type of user
-|-|-|-
0|User|None|Everyone and anyone
1|Junior Mod|Remove content. Flag accounts for higher review.|Helpful users
2|Senior Mod|Issue 24hr bans|Particularly helpful users with a good track record 
3|Junior Admin|Issue permanent bans. Promote/demote users up to level 2 |Non-developer admins.
4|Senior Admin|See IP/tech info not visible to lower ranks.|Trust+Safety
5|Deputy Owner|Promote/demote users up to level 4|Active contributors and developers
6|Owner|Direct Heroku/database access|captainmeta4. Maybe a select few others.

## Specifications

### Stack 

Layer|Tech
-|-
Host|Heroku
WSGI|Gunicorn
Server|Python Flask
ORM|SQLalchemy
Database|PostgreSQL

### Security

1. Password column is salted and hashed - no plaintext
2. Failure to login error does not specify if username or password is incorrect
3. Industry standard cryptography (or better, where possible) used everywhere appropriate

## Budget

During development, free resources are used. As the platform is launched, resources will be upgraded/migrated to paid variants

Service|Plan|Function|Justification|$/month
-|-|-|-|-
Heroku PostgreSQL|Standard 0|Database|Rollbacks, fork+follow, no row limit, 64GB storage|$50
Adminium|Startup|Database Administration|Removes 5 table cap|$10
Heroku Dynos|Hobby|Run the server|Performance metrics, no sleeping|$7
Papertrail|Choklad|Logging|Log searching beyond 2 days not yet needed |$0
**Total**||||$67
