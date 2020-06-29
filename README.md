<p align="center">
<img src="https://raw.githubusercontent.com/ruqqus/ruqqus/master/ruqqus/assets/images/logo/ruqqus_text_logo.png" width="250"/>
</p>

<hr>

# Ruqqus

Ruqqus is an open-source platform for online communities, free of censorship and moderator abuse by design.

![Build status](https://travis-ci.com/ruqqus/ruqqus.svg?branch=master) ![Snyk Vulnerabilities for GitHub Repo](https://img.shields.io/snyk/vulnerabilities/github/ruqqus/ruqqus) [![Website](https://img.shields.io/website/https/www.ruqqus.com?down_color=red&down_message=down&up_message=up)](https://www.ruqqus.com) ![GitHub language count](https://img.shields.io/github/languages/count/ruqqus/ruqqus) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/ruqqus/ruqqus) [![](https://img.shields.io/discord/599258778520518676)](https://ruqqus.com/discord)

<p align="center">
<img src="https://raw.githubusercontent.com/ruqqus/ruqqus/master/ruqqus/assets/images/preview-images/ruqqus_demo.png" width="720"/>
</p>

## Features

- Moderator power limited by design
- No ads
- US-based servers
- Mobile friendly
- Dark mode

## Why Ruqqus?

A moderator has the power to "kick" a user-submitted post from their community (guild) but never delete it off the platform entirely. Kicked posts end up in a catch-all guild called [+general](https://ruqqus.com/+general). Content that violates the [site-wide policy](https://ruqqus.com/help/terms) is removed by the core team.

Moderators, called guild masters, can only moderate a maximum of 10 guilds.

We do not serve ads. Put simply, advertisements lead to censorship. Ruqqus is funded out-of-pocket by the core team and through donations from users.

Ruqqus is responsive and mobile browser-friendly.

## Getting started

An account is not required to browse Ruqqus but we recommend creating one.

**1. Create an account**

[Sign up](https://ruqqus.com/signup?ref=ruqqus) in seconds, no email required. With a Ruqqus account, you can vote and comment on posts as well as join guilds.

**2. Join some guilds**

After signing up, we recommend you join some guilds. Your home feed will be populated by content from guilds you've joined.

**3. Create a post**

On Ruqqus, you can share links or text posts.

## Contributing

Pull requests are welcome! For major changes, please open an issue to discuss what you would like to change.

## Sponsors

As an open-source project, we are supported by the community. If you would like to support the development of Ruqqus, please consider [making a donation](https://ruqqus.com/help/donate) :)

**BTC** - 16JFRF4sXQ9BvY3w73MD64yPUKehhUtste

**LTC** - LNDKsNhHjiNBJ6YBWtE8io8H1W3Fv5mtEd

**ETH** - 0x4301c31B81C2C66f5aaDFC1ec75861ad3d3cE0cC

## Stay in touch

- [Twitter](https://twitter.com/ruqqus)
- [Discord](https://ruqqus.com/discord)
- [Twitch.tv](https://twitch.tv/captainmeta4)

## Local development

### Mac

Install dependencies

`$ pip3 install -r requirements.txt`

`$ brew install redis`

`$ brew install postgres`


Start services

`$ redis-server /usr/local/etc/redis.conf`

`$ psql postgres -a -f schema.txt`


Add test user to database (password = password)

`$ psql postgres`

```
INSERT INTO users (id, username, email, passhash, created_utc, creation_ip, tos_agreed_utc, login_nonce)
         VALUES (NEXTVAL('users_id_seq'), 'ruqqie', 'ruqqie@ruqqus.com', 'pbkdf2:sha512:150000$vmPzuBFj$24cde8a6305b7c528b0428b1e87f256c65741bb035b4356549c13e745cc0581701431d5a2297d98501fcf20367791b4334dcd19cf063a6e60195abe8214f91e8',
         1592672337, '127.0.0.1', 1592672337, 1);
```


Add this line to `/etc/hosts`

`127.0.0.1 ruqqus.localhost`


Refresh DNS

`$ sudo killall -HUP mDNSResponder`


Create environment variables

`$ export domain=ruqqus.localhost:8000`

`$ export REDIS_URL=redis://localhost:6379`

`$ export DATABASE_URL=postgres://localhost:5432/postgres`

`$ export PYTHONPATH=$(/path/to/ruqqus/root)`

`$ export MASTER_KEY=$(openssl rand -base64 32)`


Run Ruqqus

`$ gunicorn ruqqus.__main__:app -w 3 -k gevent --worker-connections 6 --preload --max-requests 500 --max-requests-jitter 50`


## License
[MPL-2.0](https://github.com/ruqqus/ruqqus/blob/master/LICENSE)

