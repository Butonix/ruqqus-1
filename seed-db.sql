--
-- PostgreSQL database dump
--

-- Dumped from database version 12.5
-- Dumped by pg_dump version 12.3

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

--
-- Data for Name: badge_defs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.badge_defs (id, name, description, icon, kind, rank, qualification_expr) FROM stdin;
3	Code Contributor	Contributed to Ruqqus source code	git.png	3	3	\N
4	White Hat	Responsibly reported a security issue	whitehat.png	3	3	\N
7	Sitebreaker	Inadvertantly broke Ruqqus	sitebreaker.png	3	2	\N
8	Unsilenced	Ruqqus rejected a foreign order to take down this user's content.	unsilenced.png	3	4	\N
1	Alpha User	Joined Ruqqus during open alpha	alpha.png	4	4	\N
6	Beta User	Joined Ruqqus during open beta	beta.png	4	3	\N
9	Unknown	Ruqqus rejected a foreign order to turn over this user's information	unknowable.png	3	4	\N
2	Verified Email	Verified Email	mail.png	1	1	v.is_activated
13	New User	Been on Ruqqus for less than 30 days	baby.png	1	1	v.age < 2592000
15	Idea Maker	Had a good idea for Ruqqus which was implemented by the developers	idea.png	3	2	\N
16	Game Night Participant	Participated in a Ruqqus community gaming event	game-participant.png	3	2	\N
17	Game Night Finalist	Had a top finish in a Ruqqus community gaming event	game-highfinish.png	3	3	\N
18	Artisan	Contributed to Ruqqus artwork or text	art.png	3	3	\N
20	Dumpster Arsonist	Awarded to 8535 tenacious users who managed to sign up for Ruqqus while the servers were getting crushed	dumpsterfire.png	5	6	\N
19	Fire Extinguisher	Awarded to users who provide major technical expertise. Current awardees: @mutageno, @AmoralAtBest, @p2hang	fire.png	5	5	\N
25	Lab Rat	Helped test features in development	labrat.png	3	3	\N
21	Bronze Patron	Contributed at least $1/month	patreon-1.png	4	1	\N
22	Silver Patron	Contributed at least $5/month	patreon-2.png	4	2	\N
23	Gold Patron	Contributed at least $20/month	patreon-3.png	4	3	\N
24	Diamond Patron	Contributed at least $50/month	patreon-4.png	4	4	\N
58	Diamond Recruiter	Recruited 1000 friends to join Ruqqus	recruit-1000.png	1	4	v.referral_count >= 1000
10	Bronze Recruiter	Recruited 1 friend to join Ruqqus	recruit-1.png	1	1	v.referral_count>=1 and v.referral_count<9
11	Silver Recruiter	Recruited 10 friends to join Ruqqus	recruit-10.png	1	2	v.referral_count>=10 and v.referral_count <= 99
12	Gold Recruiter	Recruited 100 friends to join Ruqqus	recruit-100.png	1	3	v.referral_count>=100 and v.referral_count <=999
14	Charter Supporter	Financially supported Ruqqus during start-up	charter.png	4	4	\N
59	One Year	On Ruqqus for one year	year-1.png	1	5	v.age_string=="1 year ago"
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.categories (id, color, visible, name, description, icon, is_nsfw) FROM stdin;
1	805ad5	t	Arts		fa-palette	f
2	805ad5	t	Business		fa-chart-line	f
3	805ad5	t	Culture		fa-users	f
4	805ad5	t	Discussion		fa-podium	f
5	805ad5	t	Entertainment		fa-theater-masks	f
6	805ad5	t	Gaming		fa-alien-monster	f
8	805ad5	t	Health		fa-heart	f
9	805ad5	t	Lifestyle		fa-tshirt	f
10	805ad5	t	Memes		fa-grin	f
11	805ad5	t	News		fa-newspaper	f
13	805ad5	t	Science		fa-flask	f
14	805ad5	t	Sports		fa-baseball-ball	f
15	805ad5	t	Technology		fa-microchip	f
7	805ad5	t	Hobbies		fa-wrench	f
12	805ad5	t	Politics		fa-university	f
\.


--
-- Data for Name: images; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.images (id, state, text, number) FROM stdin;
10	SD	Mount Rushmore, South Dakota	1
11	ME	Acadia National Park, Maine	1
14	UT	Arches National Park, Utah	1
15	NV	Las Vegas, NV	1
12	NY	Freedom Tower, New York	1
13	SC	The Peachoid, South Carolina	1
16	NH	Kancamangus Highway, New Hampshire	2
17	FL	Everglades, Florida	1
18	MT	Glacier National Park, Montana	1
19	WY	Jackson Hole Valley, Wyoming	1
2	AK	Mount Denali, Alaska	1
3	AZ	Horseshoe Bend, Arizona	1
4	CA	Redwood National Forest, California	1
5	DC	Lincoln Memorial, Washington DC	1
6	MA	USS Constitution, Massachusetts	1
7	NE	Downtown Omaha, Nebraska	1
9	OK	Gaylord Stadium, Oklahoma	1
\.


--
-- Data for Name: subcategories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.subcategories (id, cat_id, name, description, _visible) FROM stdin;
85	2	Startups	\N	\N
86	3	Architecture	\N	\N
109	13	Space	\N	\N
87	3	Philosophy	\N	\N
88	3	Cuisine	\N	\N
9	1	Photography		\N
10	1	Music		\N
11	2	Finance		\N
43	10	Political		\N
44	10	Offensive		\N
89	5	Influencers	\N	\N
23	5	News		\N
67	14	Combat		\N
90	14	Individual	\N	\N
91	14	Team	\N	\N
92	14	Extreme	\N	\N
93	14	Partner	\N	\N
95	15	Computers	\N	\N
96	15	Mechanics	\N	\N
75	15	Help		\N
74	15	News		\N
97	15	Engineering	\N	\N
60	13	News		\N
98	13	Hard Sciences	\N	\N
99	13	Soft Sciences	\N	\N
100	13	Natural Sciences	\N	\N
101	13	Mathematics	\N	\N
55	12	News		\N
33	7	Skills		\N
102	9	Career	\N	\N
103	9	Personal Finance	\N	\N
38	9	Beauty		\N
76	3	Counter-Culture	\N	\N
78	1	Sculpture	\N	\N
79	9	Animals	\N	\N
8	1	Film & TV		\N
80	1	Dance	\N	\N
81	1	Literature	\N	\N
82	1	Theater	\N	\N
83	2	Management	\N	\N
84	2	Product	\N	\N
37	9	Fashion		\N
104	10	Wholesome	\N	\N
105	8	Support	\N	\N
106	1	Visual Arts	\N	\N
107	6	Puzzle	\N	\N
108	12	Identity Politics	\N	\N
13	2	Entrepreneurship		\N
14	3	History		\N
15	3	Language		\N
16	3	Religion		\N
17	4	Casual Discussion		\N
18	4	Serious		\N
19	4	Drama		\N
20	4	Ruqqus Meta		\N
21	4	Q&A		\N
22	5	Celebrities		\N
24	5	Film & TV		\N
25	6	PC		\N
26	6	Console		\N
27	6	Tabletop		\N
28	6	Gaming news		\N
29	6	Development		\N
30	7	Crafts		\N
31	7	Outdoors		\N
32	7	DIY		\N
34	8	Medical		\N
35	8	Fitness		\N
36	8	Mental Health		\N
39	9	Food		\N
40	9	Relationships		\N
45	11	Local		\N
46	11	North America		\N
47	11	World		\N
48	11	Upbeat		\N
49	12	Left		\N
50	12	Right		\N
51	12	Authoritarian		\N
52	12	Libertarian		\N
53	12	Activism		\N
69	15	Gadgets		\N
70	15	Programming		\N
71	15	Hardware		\N
72	15	Software		\N
41	10	Casual		\N
42	10	Dank		\N
\.


--
-- Data for Name: titles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.titles (id, is_before, text, qualification_expr, requirement_string, color, kind, background_color_1, background_color_2, gradient_angle, box_shadow_color, text_shadow_color) FROM stdin;
9	f	, Guildmaker	v.boards_created.first()	Create your first Guild	aa8855	1	\N	\N	0	\N	\N
27	f	, the Innovative	v.has_badge(15)	Had a good idea for Ruqqus	603abb	1	\N	\N	0	\N	\N
22	f	 the Likeable	v.follower_count>=10	Have at least 10 subscribers	5555dd	1	\N	\N	0	\N	\N
23	f	 the Popular	v.follower_count>=100	Have at least 100 subscribers	5555dd	1	\N	\N	0	\N	\N
16	f	 the Spymaster	v.has_badge(4)	Responsibly report a security issue to us	666666	3	\N	\N	0	\N	\N
8	f	, the Invited	v.referred_by	Joined Ruqqus from another user's referral	55aa55	4	\N	\N	0	\N	\N
28	f	 the Gamer	v.has_badge(16)	Participate in Ruqqus gaming night	bb00bb	1	\N	\N	0	\N	\N
29	f	 [Level 1337]	v.has_badge(17)	Earn a top finish in a Ruqqus gaming night	aaaa66	1	\N	\N	0	\N	\N
4	f	, Breaker of Ruqqus	v.has_badge(7)	Inadvertently break Ruqqus	dd5555	3	\N	\N	0	\N	\N
17	f	, the Unsilenced	v.has_badge(8)	We rejected a foreign order to take down your content	666666	3	\N	\N	0	\N	\N
5	f	 the Codesmith	v.has_badge(3)	Make a contribution to the Ruqqus codebase	5555dd	3	\N	\N	0	\N	\N
6	f	, Early Adopter	v.has_badge(6)	Joined during open beta	aaaa22	4	\N	\N	0	\N	\N
7	f	, Very Early Adopter	v.has_badge(1)	Joined during open alpha	5555ff	4	\N	\N	0	\N	\N
21	f	 the Friendly	v.follower_count>=1	Have at least 1 subscriber	5555dd	1	\N	\N	0	\N	\N
24	f	 the Influential	v.follower_count>=1000	Have at least 1,000 subscribers	5555dd	1	\N	\N	0	\N	\N
25	f	, the Famous	v.follower_count>=10000	Have at least 10,000 subscribers	5555dd	1	\N	\N	0	\N	\N
26	f	 the Generous	v.has_badge(14)	Financially supported Ruqqus during start-up	bb00bb	4	\N	\N	0	\N	\N
18	f	, the Unknown	v.has_badge(9)	We rejected a foreign order for your user information	666666	3	\N	\N	0	\N	\N
19	f	, Bane of Tyrants	v.has_badge(8) and v.has_badge(9)	We rejected foreign orders for your information and to take down your content.	666666	3	\N	\N	0	\N	\N
30	f	 the Artisan	v.has_badge(18)	Made a contribution to Ruqqus text or art.	5555dd	3	\N	\N	0	\N	\N
20	f	 the Hot	v.submissions.filter(Submission.score_top>=100).count()	Get at least 100 Reputation from a single post.	dd5555	1	\N	\N	0	\N	\N
31	f	 the Dumpster Arsonist	v.has_badge(20)	Joined Ruqqus despite the flood of users crashing the site	885588	4	\N	\N	0	\N	\N
40	f	 the Test Dummy	v.has_badge(25)	Help test features in development	5555dd	3	\N	\N	\N	\N	\N
10	f	, Guildbuilder	v.boards_created.filter(Board.stored_subscriber_count>=10).first()	A Guild you created grows past 10 members.	aa8855	1	\N	\N	0	\N	\N
11	f	, Guildsmith	v.boards_created.filter(Board.stored_subscriber_count>=100).first()	A Guild you created grows past 100 members.	aa8855	1	\N	\N	0	\N	\N
12	f	, Guildmaster	v.boards_created.filter(Board.stored_subscriber_count>=1000).first()	A Guild you created grows past 1,000 members.	aa8855	1	\N	\N	0	\N	\N
13	f	, Arch Guildmaster	v.boards_created.filter(Board.stored_subscriber_count>=10000).first()	A Guild you created grows past 10,000 members.	aa8855	1	\N	\N	0	\N	\N
14	f	, Guildlord	v.boards_created.filter(Board.stored_subscriber_count>=100000).first()	A Guild you created grows past 100,000 members.	aa8855	1	\N	\N	0	\N	\N
15	f	, Ultimate Guildlord	v.boards_created.filter(Board.stored_subscriber_count>=1000000).first()	A Guild you created grows past 1,000,000 members.	aa8855	1	\N	\N	0	\N	\N
73	f	, Diamond Recruiter	v.referral_count>=1000	Refer 1000 friends to join Ruqqus	bb00bb	1	\N	\N	\N	\N	\N
1	f	, Bronze Recruiter	v.referral_count>=1	Refer 1 friend to join Ruqqus.	bb00bb	1	\N	\N	0	\N	\N
2	f	, Silver Recruiter	v.referral_count>=10	Refer 10 friends to join Ruqqus.	bb00bb	1	\N	\N	0	\N	\N
3	f	, Gold Recruiter	v.referral_count>=100	Refer 100 friends to join Ruqqus.	bb00bb	1	\N	\N	0	\N	\N
\.


--
-- Name: badge_list_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.badge_list_id_seq', 59, true);


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.categories_id_seq', 15, true);


--
-- Name: images_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.images_id_seq', 19, true);


--
-- Name: subcategories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.subcategories_id_seq', 109, true);


--
-- Name: titles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.titles_id_seq', 73, true);


--
-- PostgreSQL database dump complete
--

