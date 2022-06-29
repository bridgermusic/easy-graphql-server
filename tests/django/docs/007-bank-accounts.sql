BEGIN
;
SELECT "django_bankaccount"."id", "django_bankaccount"."iban", "django_bankaccount"."owner_id", "auth_user"."id", "auth_user"."username" FROM "django_bankaccount" INNER JOIN "auth_user" ON ("django_bankaccount"."owner_id" = "auth_user"."id") WHERE ("django_bankaccount"."owner_id" = 131 AND "django_bankaccount"."owner_id" = 131) ORDER BY "django_bankaccount"."id" ASC
