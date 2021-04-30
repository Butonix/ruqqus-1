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

INSERT INTO public.badge_defs VALUES (3, 'Code Contributor', 'Contributed to Ruqqus source code', 'git.png', 3, 3, NULL);
INSERT INTO public.badge_defs VALUES (4, 'White Hat', 'Responsibly reported a security issue', 'whitehat.png', 3, 3, NULL);
INSERT INTO public.badge_defs VALUES (7, 'Sitebreaker', 'Inadvertantly broke Ruqqus', 'sitebreaker.png', 3, 2, NULL);
INSERT INTO public.badge_defs VALUES (8, 'Unsilenced', 'Ruqqus rejected a foreign order to take down this user''s content.', 'unsilenced.png', 3, 4, NULL);
INSERT INTO public.badge_defs VALUES (1, 'Alpha User', 'Joined Ruqqus during open alpha', 'alpha.png', 4, 4, NULL);
INSERT INTO public.badge_defs VALUES (6, 'Beta User', 'Joined Ruqqus during open beta', 'beta.png', 4, 3, NULL);
INSERT INTO public.badge_defs VALUES (9, 'Unknown', 'Ruqqus rejected a foreign order to turn over this user''s information', 'unknowable.png', 3, 4, NULL);
INSERT INTO public.badge_defs VALUES (2, 'Verified Email', 'Verified Email', 'mail.png', 1, 1, 'v.is_activated');
INSERT INTO public.badge_defs VALUES (13, 'New User', 'Been on Ruqqus for less than 30 days', 'baby.png', 1, 1, 'v.age < 2592000');
INSERT INTO public.badge_defs VALUES (15, 'Idea Maker', 'Had a good idea for Ruqqus which was implemented by the developers', 'idea.png', 3, 2, NULL);
INSERT INTO public.badge_defs VALUES (16, 'Game Night Participant', 'Participated in a Ruqqus community gaming event', 'game-participant.png', 3, 2, NULL);
INSERT INTO public.badge_defs VALUES (17, 'Game Night Finalist', 'Had a top finish in a Ruqqus community gaming event', 'game-highfinish.png', 3, 3, NULL);
INSERT INTO public.badge_defs VALUES (18, 'Artisan', 'Contributed to Ruqqus artwork or text', 'art.png', 3, 3, NULL);
INSERT INTO public.badge_defs VALUES (20, 'Dumpster Arsonist', 'Awarded to 8535 tenacious users who managed to sign up for Ruqqus while the servers were getting crushed', 'dumpsterfire.png', 5, 6, NULL);
INSERT INTO public.badge_defs VALUES (19, 'Fire Extinguisher', 'Awarded to users who provide major technical expertise. Current awardees: @mutageno, @AmoralAtBest, @p2hang', 'fire.png', 5, 5, NULL);
INSERT INTO public.badge_defs VALUES (25, 'Lab Rat', 'Helped test features in development', 'labrat.png', 3, 3, NULL);
INSERT INTO public.badge_defs VALUES (21, 'Bronze Patron', 'Contributed at least $1/month', 'patreon-1.png', 4, 1, NULL);
INSERT INTO public.badge_defs VALUES (22, 'Silver Patron', 'Contributed at least $5/month', 'patreon-2.png', 4, 2, NULL);
INSERT INTO public.badge_defs VALUES (23, 'Gold Patron', 'Contributed at least $20/month', 'patreon-3.png', 4, 3, NULL);
INSERT INTO public.badge_defs VALUES (24, 'Diamond Patron', 'Contributed at least $50/month', 'patreon-4.png', 4, 4, NULL);
INSERT INTO public.badge_defs VALUES (58, 'Diamond Recruiter', 'Recruited 1000 friends to join Ruqqus', 'recruit-1000.png', 1, 4, 'v.referral_count >= 1000');
INSERT INTO public.badge_defs VALUES (10, 'Bronze Recruiter', 'Recruited 1 friend to join Ruqqus', 'recruit-1.png', 1, 1, 'v.referral_count>=1 and v.referral_count<9');
INSERT INTO public.badge_defs VALUES (11, 'Silver Recruiter', 'Recruited 10 friends to join Ruqqus', 'recruit-10.png', 1, 2, 'v.referral_count>=10 and v.referral_count <= 99');
INSERT INTO public.badge_defs VALUES (12, 'Gold Recruiter', 'Recruited 100 friends to join Ruqqus', 'recruit-100.png', 1, 3, 'v.referral_count>=100 and v.referral_count <=999');
INSERT INTO public.badge_defs VALUES (14, 'Charter Supporter', 'Financially supported Ruqqus during start-up', 'charter.png', 4, 4, NULL);
INSERT INTO public.badge_defs VALUES (59, 'One Year', 'On Ruqqus for one year', 'year-1.png', 1, 5, 'v.age_string=="1 year ago"');


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.categories VALUES (1, '805ad5', true, 'Arts', '', 'fa-palette', false);
INSERT INTO public.categories VALUES (2, '805ad5', true, 'Business', '', 'fa-chart-line', false);
INSERT INTO public.categories VALUES (3, '805ad5', true, 'Culture', '', 'fa-users', false);
INSERT INTO public.categories VALUES (4, '805ad5', true, 'Discussion', '', 'fa-podium', false);
INSERT INTO public.categories VALUES (5, '805ad5', true, 'Entertainment', '', 'fa-theater-masks', false);
INSERT INTO public.categories VALUES (6, '805ad5', true, 'Gaming', '', 'fa-alien-monster', false);
INSERT INTO public.categories VALUES (8, '805ad5', true, 'Health', '', 'fa-heart', false);
INSERT INTO public.categories VALUES (9, '805ad5', true, 'Lifestyle', '', 'fa-tshirt', false);
INSERT INTO public.categories VALUES (10, '805ad5', true, 'Memes', '', 'fa-grin', false);
INSERT INTO public.categories VALUES (11, '805ad5', true, 'News', '', 'fa-newspaper', false);
INSERT INTO public.categories VALUES (13, '805ad5', true, 'Science', '', 'fa-flask', false);
INSERT INTO public.categories VALUES (14, '805ad5', true, 'Sports', '', 'fa-baseball-ball', false);
INSERT INTO public.categories VALUES (15, '805ad5', true, 'Technology', '', 'fa-microchip', false);
INSERT INTO public.categories VALUES (7, '805ad5', true, 'Hobbies', '', 'fa-wrench', false);
INSERT INTO public.categories VALUES (12, '805ad5', true, 'Politics', '', 'fa-university', false);


--
-- Data for Name: images; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.images VALUES (10, 'SD', 'Mount Rushmore, South Dakota', 1);
INSERT INTO public.images VALUES (11, 'ME', 'Acadia National Park, Maine', 1);
INSERT INTO public.images VALUES (14, 'UT', 'Arches National Park, Utah', 1);
INSERT INTO public.images VALUES (15, 'NV', 'Las Vegas, NV', 1);
INSERT INTO public.images VALUES (12, 'NY', 'Freedom Tower, New York', 1);
INSERT INTO public.images VALUES (13, 'SC', 'The Peachoid, South Carolina', 1);
INSERT INTO public.images VALUES (16, 'NH', 'Kancamangus Highway, New Hampshire', 2);
INSERT INTO public.images VALUES (17, 'FL', 'Everglades, Florida', 1);
INSERT INTO public.images VALUES (18, 'MT', 'Glacier National Park, Montana', 1);
INSERT INTO public.images VALUES (19, 'WY', 'Jackson Hole Valley, Wyoming', 1);
INSERT INTO public.images VALUES (2, 'AK', 'Mount Denali, Alaska', 1);
INSERT INTO public.images VALUES (3, 'AZ', 'Horseshoe Bend, Arizona', 1);
INSERT INTO public.images VALUES (4, 'CA', 'Redwood National Forest, California', 1);
INSERT INTO public.images VALUES (5, 'DC', 'Lincoln Memorial, Washington DC', 1);
INSERT INTO public.images VALUES (6, 'MA', 'USS Constitution, Massachusetts', 1);
INSERT INTO public.images VALUES (7, 'NE', 'Downtown Omaha, Nebraska', 1);
INSERT INTO public.images VALUES (9, 'OK', 'Gaylord Stadium, Oklahoma', 1);


--
-- Data for Name: subcategories; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.subcategories VALUES (85, 2, 'Startups', NULL, NULL);
INSERT INTO public.subcategories VALUES (86, 3, 'Architecture', NULL, NULL);
INSERT INTO public.subcategories VALUES (109, 13, 'Space', NULL, NULL);
INSERT INTO public.subcategories VALUES (87, 3, 'Philosophy', NULL, NULL);
INSERT INTO public.subcategories VALUES (88, 3, 'Cuisine', NULL, NULL);
INSERT INTO public.subcategories VALUES (9, 1, 'Photography', '', NULL);
INSERT INTO public.subcategories VALUES (10, 1, 'Music', '', NULL);
INSERT INTO public.subcategories VALUES (11, 2, 'Finance', '', NULL);
INSERT INTO public.subcategories VALUES (43, 10, 'Political', '', NULL);
INSERT INTO public.subcategories VALUES (44, 10, 'Offensive', '', NULL);
INSERT INTO public.subcategories VALUES (89, 5, 'Influencers', NULL, NULL);
INSERT INTO public.subcategories VALUES (23, 5, 'News', '', NULL);
INSERT INTO public.subcategories VALUES (67, 14, 'Combat', '', NULL);
INSERT INTO public.subcategories VALUES (90, 14, 'Individual', NULL, NULL);
INSERT INTO public.subcategories VALUES (91, 14, 'Team', NULL, NULL);
INSERT INTO public.subcategories VALUES (92, 14, 'Extreme', NULL, NULL);
INSERT INTO public.subcategories VALUES (93, 14, 'Partner', NULL, NULL);
INSERT INTO public.subcategories VALUES (95, 15, 'Computers', NULL, NULL);
INSERT INTO public.subcategories VALUES (96, 15, 'Mechanics', NULL, NULL);
INSERT INTO public.subcategories VALUES (75, 15, 'Help', '', NULL);
INSERT INTO public.subcategories VALUES (74, 15, 'News', '', NULL);
INSERT INTO public.subcategories VALUES (97, 15, 'Engineering', NULL, NULL);
INSERT INTO public.subcategories VALUES (60, 13, 'News', '', NULL);
INSERT INTO public.subcategories VALUES (98, 13, 'Hard Sciences', NULL, NULL);
INSERT INTO public.subcategories VALUES (99, 13, 'Soft Sciences', NULL, NULL);
INSERT INTO public.subcategories VALUES (100, 13, 'Natural Sciences', NULL, NULL);
INSERT INTO public.subcategories VALUES (101, 13, 'Mathematics', NULL, NULL);
INSERT INTO public.subcategories VALUES (55, 12, 'News', '', NULL);
INSERT INTO public.subcategories VALUES (33, 7, 'Skills', '', NULL);
INSERT INTO public.subcategories VALUES (102, 9, 'Career', NULL, NULL);
INSERT INTO public.subcategories VALUES (103, 9, 'Personal Finance', NULL, NULL);
INSERT INTO public.subcategories VALUES (38, 9, 'Beauty', '', NULL);
INSERT INTO public.subcategories VALUES (76, 3, 'Counter-Culture', NULL, NULL);
INSERT INTO public.subcategories VALUES (78, 1, 'Sculpture', NULL, NULL);
INSERT INTO public.subcategories VALUES (79, 9, 'Animals', NULL, NULL);
INSERT INTO public.subcategories VALUES (8, 1, 'Film & TV', '', NULL);
INSERT INTO public.subcategories VALUES (80, 1, 'Dance', NULL, NULL);
INSERT INTO public.subcategories VALUES (81, 1, 'Literature', NULL, NULL);
INSERT INTO public.subcategories VALUES (82, 1, 'Theater', NULL, NULL);
INSERT INTO public.subcategories VALUES (83, 2, 'Management', NULL, NULL);
INSERT INTO public.subcategories VALUES (84, 2, 'Product', NULL, NULL);
INSERT INTO public.subcategories VALUES (37, 9, 'Fashion', '', NULL);
INSERT INTO public.subcategories VALUES (104, 10, 'Wholesome', NULL, NULL);
INSERT INTO public.subcategories VALUES (105, 8, 'Support', NULL, NULL);
INSERT INTO public.subcategories VALUES (106, 1, 'Visual Arts', NULL, NULL);
INSERT INTO public.subcategories VALUES (107, 6, 'Puzzle', NULL, NULL);
INSERT INTO public.subcategories VALUES (108, 12, 'Identity Politics', NULL, NULL);
INSERT INTO public.subcategories VALUES (13, 2, 'Entrepreneurship', '', NULL);
INSERT INTO public.subcategories VALUES (14, 3, 'History', '', NULL);
INSERT INTO public.subcategories VALUES (15, 3, 'Language', '', NULL);
INSERT INTO public.subcategories VALUES (16, 3, 'Religion', '', NULL);
INSERT INTO public.subcategories VALUES (17, 4, 'Casual Discussion', '', NULL);
INSERT INTO public.subcategories VALUES (18, 4, 'Serious', '', NULL);
INSERT INTO public.subcategories VALUES (19, 4, 'Drama', '', NULL);
INSERT INTO public.subcategories VALUES (20, 4, 'Ruqqus Meta', '', NULL);
INSERT INTO public.subcategories VALUES (21, 4, 'Q&A', '', NULL);
INSERT INTO public.subcategories VALUES (22, 5, 'Celebrities', '', NULL);
INSERT INTO public.subcategories VALUES (24, 5, 'Film & TV', '', NULL);
INSERT INTO public.subcategories VALUES (25, 6, 'PC', '', NULL);
INSERT INTO public.subcategories VALUES (26, 6, 'Console', '', NULL);
INSERT INTO public.subcategories VALUES (27, 6, 'Tabletop', '', NULL);
INSERT INTO public.subcategories VALUES (28, 6, 'Gaming news', '', NULL);
INSERT INTO public.subcategories VALUES (29, 6, 'Development', '', NULL);
INSERT INTO public.subcategories VALUES (30, 7, 'Crafts', '', NULL);
INSERT INTO public.subcategories VALUES (31, 7, 'Outdoors', '', NULL);
INSERT INTO public.subcategories VALUES (32, 7, 'DIY', '', NULL);
INSERT INTO public.subcategories VALUES (34, 8, 'Medical', '', NULL);
INSERT INTO public.subcategories VALUES (35, 8, 'Fitness', '', NULL);
INSERT INTO public.subcategories VALUES (36, 8, 'Mental Health', '', NULL);
INSERT INTO public.subcategories VALUES (39, 9, 'Food', '', NULL);
INSERT INTO public.subcategories VALUES (40, 9, 'Relationships', '', NULL);
INSERT INTO public.subcategories VALUES (45, 11, 'Local', '', NULL);
INSERT INTO public.subcategories VALUES (46, 11, 'North America', '', NULL);
INSERT INTO public.subcategories VALUES (47, 11, 'World', '', NULL);
INSERT INTO public.subcategories VALUES (48, 11, 'Upbeat', '', NULL);
INSERT INTO public.subcategories VALUES (49, 12, 'Left', '', NULL);
INSERT INTO public.subcategories VALUES (50, 12, 'Right', '', NULL);
INSERT INTO public.subcategories VALUES (51, 12, 'Authoritarian', '', NULL);
INSERT INTO public.subcategories VALUES (52, 12, 'Libertarian', '', NULL);
INSERT INTO public.subcategories VALUES (53, 12, 'Activism', '', NULL);
INSERT INTO public.subcategories VALUES (69, 15, 'Gadgets', '', NULL);
INSERT INTO public.subcategories VALUES (70, 15, 'Programming', '', NULL);
INSERT INTO public.subcategories VALUES (71, 15, 'Hardware', '', NULL);
INSERT INTO public.subcategories VALUES (72, 15, 'Software', '', NULL);
INSERT INTO public.subcategories VALUES (41, 10, 'Casual', '', NULL);
INSERT INTO public.subcategories VALUES (42, 10, 'Dank', '', NULL);


--
-- Data for Name: titles; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.titles VALUES (9, false, ', Guildmaker', 'v.boards_created.first()', 'Create your first Guild', 'aa8855', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (27, false, ', the Innovative', 'v.has_badge(15)', 'Had a good idea for Ruqqus', '603abb', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (22, false, ' the Likeable', 'v.follower_count>=10', 'Have at least 10 subscribers', '5555dd', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (23, false, ' the Popular', 'v.follower_count>=100', 'Have at least 100 subscribers', '5555dd', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (16, false, ' the Spymaster', 'v.has_badge(4)', 'Responsibly report a security issue to us', '666666', 3, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (8, false, ', the Invited', 'v.referred_by', 'Joined Ruqqus from another user''s referral', '55aa55', 4, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (28, false, ' the Gamer', 'v.has_badge(16)', 'Participate in Ruqqus gaming night', 'bb00bb', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (29, false, ' [Level 1337]', 'v.has_badge(17)', 'Earn a top finish in a Ruqqus gaming night', 'aaaa66', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (4, false, ', Breaker of Ruqqus', 'v.has_badge(7)', 'Inadvertently break Ruqqus', 'dd5555', 3, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (17, false, ', the Unsilenced', 'v.has_badge(8)', 'We rejected a foreign order to take down your content', '666666', 3, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (5, false, ' the Codesmith', 'v.has_badge(3)', 'Make a contribution to the Ruqqus codebase', '5555dd', 3, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (6, false, ', Early Adopter', 'v.has_badge(6)', 'Joined during open beta', 'aaaa22', 4, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (7, false, ', Very Early Adopter', 'v.has_badge(1)', 'Joined during open alpha', '5555ff', 4, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (21, false, ' the Friendly', 'v.follower_count>=1', 'Have at least 1 subscriber', '5555dd', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (24, false, ' the Influential', 'v.follower_count>=1000', 'Have at least 1,000 subscribers', '5555dd', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (25, false, ', the Famous', 'v.follower_count>=10000', 'Have at least 10,000 subscribers', '5555dd', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (26, false, ' the Generous', 'v.has_badge(14)', 'Financially supported Ruqqus during start-up', 'bb00bb', 4, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (18, false, ', the Unknown', 'v.has_badge(9)', 'We rejected a foreign order for your user information', '666666', 3, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (19, false, ', Bane of Tyrants', 'v.has_badge(8) and v.has_badge(9)', 'We rejected foreign orders for your information and to take down your content.', '666666', 3, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (30, false, ' the Artisan', 'v.has_badge(18)', 'Made a contribution to Ruqqus text or art.', '5555dd', 3, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (20, false, ' the Hot', 'v.submissions.filter(Submission.score_top>=100).count()', 'Get at least 100 Reputation from a single post.', 'dd5555', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (31, false, ' the Dumpster Arsonist', 'v.has_badge(20)', 'Joined Ruqqus despite the flood of users crashing the site', '885588', 4, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (40, false, ' the Test Dummy', 'v.has_badge(25)', 'Help test features in development', '5555dd', 3, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.titles VALUES (10, false, ', Guildbuilder', 'v.boards_created.filter(Board.stored_subscriber_count>=10).first()', 'A Guild you created grows past 10 members.', 'aa8855', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (11, false, ', Guildsmith', 'v.boards_created.filter(Board.stored_subscriber_count>=100).first()', 'A Guild you created grows past 100 members.', 'aa8855', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (12, false, ', Guildmaster', 'v.boards_created.filter(Board.stored_subscriber_count>=1000).first()', 'A Guild you created grows past 1,000 members.', 'aa8855', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (13, false, ', Arch Guildmaster', 'v.boards_created.filter(Board.stored_subscriber_count>=10000).first()', 'A Guild you created grows past 10,000 members.', 'aa8855', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (14, false, ', Guildlord', 'v.boards_created.filter(Board.stored_subscriber_count>=100000).first()', 'A Guild you created grows past 100,000 members.', 'aa8855', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (15, false, ', Ultimate Guildlord', 'v.boards_created.filter(Board.stored_subscriber_count>=1000000).first()', 'A Guild you created grows past 1,000,000 members.', 'aa8855', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (73, false, ', Diamond Recruiter', 'v.referral_count>=1000', 'Refer 1000 friends to join Ruqqus', 'bb00bb', 1, NULL, NULL, NULL, NULL, NULL);
INSERT INTO public.titles VALUES (1, false, ', Bronze Recruiter', 'v.referral_count>=1', 'Refer 1 friend to join Ruqqus.', 'bb00bb', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (2, false, ', Silver Recruiter', 'v.referral_count>=10', 'Refer 10 friends to join Ruqqus.', 'bb00bb', 1, NULL, NULL, 0, NULL, NULL);
INSERT INTO public.titles VALUES (3, false, ', Gold Recruiter', 'v.referral_count>=100', 'Refer 100 friends to join Ruqqus.', 'bb00bb', 1, NULL, NULL, 0, NULL, NULL);


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

