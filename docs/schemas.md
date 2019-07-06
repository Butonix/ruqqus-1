# Schemas

These are the schemas for the database. In all tables, the `id` column is the Primary Key.

May be slightly out of date as features are developed.

## Users

Column|Type|Options
-|-|-
id|int|NOT NULL AUTO INCREMENT
username|varchar(255)|UNIQUE NOT NULL
email|varchar(255)|UNIQUE
passhash|varchar(255)|NOT NULL
created_utc|int|NOT NULL
admin_level|int|DEFAULT 0
is_banned|bool|DEFAULT false
over_18|bool|DEFAULT false

## Submissions

Column|Type|Options
-|-|-
id|int|NOT NULL AUTO INCREMENT	
author_id|int| NOT NULL REFERENCES Users(id)			
title|charvar(255)			
url|charvar(255)			
created_utc|int|NOT NULL
is_banned|boolean|DEFAULT false
over_18|boolean|DEFAULT false

## Comments

Column|Type|Options
-|-|-
id|int| NOT NULL AUTO INCREMENT	
author_id|int|NOT NULL REFERENCES Users(id)			
body|varchar(2000)		
created_utc|int|NOT NULL		
parent_post|int			
parent_comment|int			
is_banned|bool|DEFAULT false

## Votes

Column|Type|Options
-|-|-
id|int| NOT NULL AUTO INCREMENT	
user|int|NOT NULL REFERENCES Users(id)		
is_up|bool
comment_id|int|REFERENCES Comments(id)
submission_id|int|REFERENCES Submissions(id)

## IPs

Column|Type|Options
-|-|-
id|int|NOT NULL AUTO INCREMENT
ip|varchar(40)|NOT NULL
user_id|int|NOT NULL REFERENCES Users(id)
