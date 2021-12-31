SELECT "django_person"."id", "django_person"."first_name", "django_person"."last_name", "django_person"."home_id",
  "django_house"."id", "django_house"."location", "django_house"."owner_id",
  T3."id", T3."first_name", T3."last_name", T3."home_id"
FROM "django_person"
LEFT OUTER JOIN "django_house" ON ("django_person"."home_id" = "django_house"."id")
LEFT OUTER JOIN "django_person" T3 ON ("django_house"."owner_id" = T3."id")
WHERE "django_person"."id" = 445

;

SELECT "django_house"."id", "django_house"."location", "django_house"."owner_id"
FROM "django_house"
WHERE "django_house"."owner_id" IN (445)

;

SELECT "django_person"."id", "django_person"."first_name", "django_person"."last_name", "django_person"."home_id"
FROM "django_person"
WHERE "django_person"."home_id" IN (39, 99, 100)
