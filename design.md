# Design

The purpose of this document is to clearly identify:

* Project goals
* Project requirements to meet those goals
* Project specifications to meet those requirements

## Goals

1. Provide a place where /r/The_Donald users can congregate in the event that reddit admins choose to ban /r/The_Donald

## Requirements

### General

1. To the greatest extent possible, mimic reddit functionality as it applies to /r/the_donald (Quarantine/ban status notwithstnading)
2. Use reddit oauth to validate new users and import usernames from reddit to new accounts, allowing for continuous preservation of identity
3. No advertising, donations only

### UX

1. Allow submission of links and text
2. Allow commenting on submissions
3. Allow commenting on comments
4. Allow up/down voting on submissions and comments
5. Sort submissions by new, hot, etc
6. Allow users to delete their own content

### Administration

1. Site admins can remove (hide) posts and comments
2. Site admins can ban users

## Specifications

1. Database: PostgreSQL. One table each for users, submissions, and comments
2. Server: Python Flask
3. WSGI: Gunicorn
4. Host: Heroku
