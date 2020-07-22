SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';


SET default_table_access_method = heap;

-- Insert test user (username = "ruqqie", password = "password")
INSERT INTO public.users (id, username, email, passhash, created_utc, creation_ip, tos_agreed_utc, login_nonce, admin_level    )
VALUES (NEXTVAL('public.users_id_seq'), 'ruqqie', 'ruqqie@ruqqus.com', 'pbkdf2:sha512:150000$vmPzuBFj$24cde8a6305b7c528b0428b1e87f256c65741bb035b4356549c13e745cc0581701431d5a2297d98501fcf20367791b4334dcd19cf063a6e60195abe8214f91e8',1592672337, '127.0.0.1', 1592672337, 1, 1);

INSERT INTO public.boards(name, is_banned, created_utc, description, description_html, creator_id, color) VALUES('general', 'false', 1592984412, 'board description', '<p>general description</p>+', 1, '805ad5');
INSERT INTO public.boards(name, is_banned, created_utc, description, description_html, creator_id, color) VALUES('ruqqus', 'false', 1592984412, 'board description', '<p>ruqqus description</p>+', 1, '805ad5');


COPY public.badge_defs (id, name, description, icon, kind, rank, qualification_expr) FROM stdin;
3	Code Contributor	Contributed to Ruqqus source code	git.png	3	3	\N
4	White Hat	Responsibly reported a security issue	whitehat.png	3	3	\N
7	Sitebreaker	Inadvertantly broke Ruqqus	sitebreaker.png	3	2	\N
8	Unsilenced	Ruqqus rejected a foreign order to take down this user's content.	unsilenced.png	3	4	\N
1	Alpha User	Joined Ruqqus during open alpha	alpha.png	4	4	\N
6	Beta User	Joined Ruqqus during open beta	beta.png	4	3	\N
9	Unknown	Ruqqus rejected a foreign order to turn over this user's information	unknowable.png	3	4	\N
10	Recruiter	Recruited 1 friend to join Ruqqus	recruit-1.png	1	1	v.referral_count>=1 and v.referral_count<9
11	Recruiter	Recruited 10 friends to join Ruqqus	recruit-10.png	1	2	v.referral_count>=10 and v.referral_count <= 99
12	Recruiter	Recruited 100 friends to join Ruqqus	recruit-100.png	1	3	v.referral_count>=100
2	Verified Email	Verified Email	mail.png	1	1	v.is_activated
13	New User	Been on Ruqqus for less than 30 days	baby.png	1	1	v.age < 2592000
15	Idea Maker	Had a good idea for Ruqqus which was implemented by the developers	idea.png	3	2	\N
16	Game Night Participant	Participated in a Ruqqus community gaming event	game-participant.png	3	2	\N
17	Game Night Finalist	Had a top finish in a Ruqqus community gaming event	game-highfinish.png	3	3	\N
18	Artisan	Contributed to Ruqqus artwork or text	art.png	3	3	\N
14	Charter Supporter	Financially supported Ruqqus during start-up	charter.png	4	4	\N
19	Fire Extinguisher	Awarded to @mutageno and @AmoralAtBest for contributing highly advanced technical experience and wisdom during scale-up operations resulting from the flood of new users.	fire.png	5	5	\N
20	Dumpster Arsonist	Awarded to 8535 tenacious users who managed to sign up for Ruqqus while the servers were getting crushed	dumpsterfire.png	5	6	\N
21	Bronze Patron	Contributes at least $1/month	patreon-1.png	2	1	v.patreon_pledge_cents>=100 and v.patreon_pledge_cents<500
22	Silver Patron	Contributes at least $5/month	patreon-2.png	2	2	v.patreon_pledge_cents>=500 and v.patreon_pledge_cents<2000
23	Gold Patron	Contributes at least $20/month	patreon-3.png	2	3	v.patreon_pledge_cents>=2000 and v.patreon_pledge_cents<5000
24	Diamond Patron	Contributes at least $50/month	patreon-4.png	2	4	v.patreon_pledge_cents>=5000
\.


COPY public.titles (id, is_before, text, qualification_expr, requirement_string, color, kind, background_color_1, background_color_2, gradient_angle, box_shadow_color, text_shadow_color) FROM stdin;
9	f	, Guildmaker	v.boards_created.first()	Create your first Guild	aa8855	1	\N	\N	0	\N	\N
10	f	, Guildbuilder	v.boards_created.filter(Board.subscriber_count>=10).first()	A Guild you created grows past 10 members.	aa8855	1	\N	\N	0	\N	\N
11	f	, Guildsmith	v.boards_created.filter(Board.subscriber_count>=100).first()	A Guild you created grows past 100 members.	aa8855	1	\N	\N	0	\N	\N
13	f	, Arch Guildmaster	v.boards_created.filter(Board.subscriber_count>=10000).first()	A Guild you created grows past 10,000 members.	aa8855	1	\N	\N	0	\N	\N
27	f	, the Innovative	v.has_badge(15)	Had a good idea for Ruqqus	603abb	1	\N	\N	0	\N	\N
22	f	 the Likeable	v.follower_count>=10	Have at least 10 subscribers	5555dd	1	\N	\N	0	\N	\N
23	f	 the Popular	v.follower_count>=100	Have at least 100 subscribers	5555dd	1	\N	\N	0	\N	\N
16	f	 the Spymaster	v.has_badge(4)	Responsibly report a security issue to us	666666	3	\N	\N	0	\N	\N
8	f	, the Invited	v.referred_by	Joined Ruqqus from another user's referral	55aa55	4	\N	\N	0	\N	\N
1	f	, Novice Recruiter	v.referral_count>=1	Refer 1 friend to join Ruqqus.	bb00bb	1	\N	\N	0	\N	\N
28	f	 the Gamer	v.has_badge(16)	Participate in Ruqqus gaming night	bb00bb	1	\N	\N	0	\N	\N
29	f	 [Level 1337]	v.has_badge(17)	Earn a top finish in a Ruqqus gaming night	aaaa66	1	\N	\N	0	\N	\N
4	f	, Breaker of Ruqqus	v.has_badge(7)	Inadvertently break Ruqqus	dd5555	3	\N	\N	0	\N	\N
2	f	, Expert Recruiter	v.referral_count>=10	Refer 10 friends to join Ruqqus.	bb00bb	1	\N	\N	0	\N	\N
17	f	, the Unsilenced	v.has_badge(8)	We rejected a foreign order to take down your content	666666	3	\N	\N	0	\N	\N
3	f	, Master Recruiter	v.referral_count>=100	Refer 100 friends to join Ruqqus.	bb00bb	1	\N	\N	0	\N	\N
5	f	 the Codesmith	v.has_badge(3)	Make a contribution to the Ruqqus codebase	5555dd	3	\N	\N	0	\N	\N
6	f	, Early Adopter	v.has_badge(6)	Joined during open beta	aaaa22	4	\N	\N	0	\N	\N
7	f	, Very Early Adopter	v.has_badge(1)	Joined during open alpha	5555ff	4	\N	\N	0	\N	\N
12	f	, Guildmaster	v.boards_created.filter(Board.subscriber_count>=1000).first()	A Guild you created grows past 1,000 members.	aa8855	1	\N	\N	0	\N	\N
21	f	 the Friendly	v.follower_count>=1	Have at least 1 subscriber	5555dd	1	\N	\N	0	\N	\N
24	f	 the Influential	v.follower_count>=1000	Have at least 1,000 subscribers	5555dd	1	\N	\N	0	\N	\N
25	f	, the Famous	v.follower_count>=10000	Have at least 10,000 subscribers	5555dd	1	\N	\N	0	\N	\N
26	f	 the Generous	v.has_badge(14)	Financially supported Ruqqus during start-up	bb00bb	4	\N	\N	0	\N	\N
18	f	, the Unknown	v.has_badge(9)	We rejected a foreign order for your user information	666666	3	\N	\N	0	\N	\N
20	f	 the Hot	v.submissions.filter(Submission.score>=100).first()	Get at least 100 Reputation from a single post.	dd5555	1	\N	\N	0	\N	\N
19	f	, Bane of Tyrants	v.has_badge(8) and v.has_badge(9)	We rejected foreign orders for your information and to take down your content.	666666	3	\N	\N	0	\N	\N
14	f	, Guildlord	v.boards_created.filter(Board.subscriber_count>=100000).first()	A Guild you created grows past 100,000 members.	aa8855	1	\N	\N	0	\N	\N
15	f	, Ultimate Guildlord	v.boards_created.filter(Board.subscriber_count>=1000000).first()	A Guild you created grows past 1,000,000 members.	aa8855	1	\N	\N	0	\N	\N
32	f	, Bronze Patron	v.patreon_pledge_cents>=100 and v.patreon_pledge_cents<500	Contribute at least $1/month on Patreon	aa8855	2	\N	\N	0	\N	\N
30	f	 the Artisan	v.has_badge(18)	Made a contribution to Ruqqus text or art.	5555dd	3	\N	\N	0	\N	\N
34	f	Gold Patron	v.patreon_pledge_cents>=2000 and v.patreon_pledge_cents<5000	Contribute at least $20/month on Patreon	502e0e	2	ce9632	f7ce68	5	216, 178, 84	240, 188, 120
35	f	Diamond Patron	v.patreon_pledge_cents>=5000	Contribute at least $50/month on Patreon	2a4042	2	54c0c0	89e5ee	10	88, 195, 199	191, 220, 216
31	f	 the Dumpster Arsonist	v.has_badge(20)	Joined Ruqqus despite the flood of users crashing the site	885588	4	\N	\N	0	\N	\N
33	f	Silver Patron	v.patreon_pledge_cents>=500 and v.patreon_pledge_cents<2000	Contribute at least $5/month on Patreon	30363c	2	899caa	c6d1dc	4	\N	\N
\.

