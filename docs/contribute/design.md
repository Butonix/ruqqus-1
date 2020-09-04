---
title: Ruqqus Design Doc
---

# Design

The purpose of this document is to clearly identify:

* Project goals
* Project requirements to meet those goals
* Project specifications to meet those requirements

## Goals

1. Provide a place where users deplatformed from other sites can share news, meme, and otherwise interact.

## Requirements

### General

1. To the greatest extent possible, mimic reddit functionality without allowing board moderators to censor users
2. No advertising, donations only (to avoid contractual obligations to advertisers)
3. No manipulation, fair treatment of all content.

### UX

1. Allow submission of links and text
2. Allow commenting on submissions
3. Allow commenting on comments
4. Allow up/down voting on submissions and comments
5. Sort submissions by new, hot, etc
6. Allow users to delete their own content
7. Allow users to report rule-breaking submissions and comments

### Administration

Several layers of administrative privilege will be implemented

As of 30 Aug 2020, only levels 0, 1, and 6 are in use.

Integer|Name|Permissions|Type of user
-|-|-|-
0|User|None|Everyone and anyone
1|Admin Emeritus|No permissions. Black "former admin" badge on profile.|Former employees
2|Admin|Distinguish comments. Basic, non-T&S features. |Non-tech staff (ex. Legal, HR)
3|T&S I|Remove content| Junior Devs
4|T&S II|Issue bans, view more detailed data, such as IP addresses|Senior devs
5|Deputy Owner|Add/remove lower ranks|Part owners
6|Owner|Direct Heroku/database access|Majority owners only.

## Specifications

### Stack 

Layer|Tech
-|-
Host|Heroku
WSGI|Gunicorn
Application|Python Flask
ORM|SQLalchemy
Database|PostgreSQL

### Security

1. Password column is salted and hashed - no plaintext
2. Failure to login error does not specify if username or password is incorrect
3. Industry standard cryptography (or better, where possible) used everywhere appropriate
4. Form tokens used to prevent CSRF

### Budget

During development, free resources are used. As the platform is launched, resources will be upgraded/migrated to paid variants

Service|Plan|Function|Justification|Upgrade Timing|$/month
-|-|-|-|-|-
Heroku PostgreSQL|Standard 0|Leader Database|Smallest plan with follower|As 10k row limit on free db is approached|$50
Heroku PostgreSQL|Standard 2|Follower Database|Additional memory needed for complex read operations|$200
Heroku Dyno|Performance L|Origin server|Lots of power, very memory-efficient|Already done|$500
Heroku Redis|N/A|Server-side caching|N/A|Implement when multiple origin servers are needed|N/A
**Total**|||||$750
