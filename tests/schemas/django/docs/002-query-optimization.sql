BEGIN
;
SELECT "auth_user"."id", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."home_id", "django_house"."id", "django_house"."location", "django_house"."owner_id", T3."id", T3."first_name", T3."last_name", T3."home_id" FROM "auth_user" LEFT OUTER JOIN "django_house" ON ("auth_user"."home_id" = "django_house"."id") LEFT OUTER JOIN "auth_user" T3 ON ("django_house"."owner_id" = T3."id") WHERE "auth_user"."id" = 445 LIMIT 21
;
SELECT "django_house"."id", "django_house"."location", "django_house"."owner_id" FROM "django_house" WHERE "django_house"."owner_id" IN (445) ORDER BY "django_house"."id" ASC
;
SELECT "auth_user"."id", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."home_id" FROM "auth_user" WHERE "auth_user"."home_id" IN (39, 99, 100) ORDER BY "auth_user"."id" ASC
