
CREATE SEQUENCE author_id_sequence AS BIGINT;
CREATE SEQUENCE post_id_sequence AS BIGINT;
CREATE SEQUENCE comment_id_sequence AS BIGINT;


CREATE TABLE author(
    id BIGINT PRIMARY KEY DEFAULT nextval('author_id_sequence'),
    name text UNIQUE
);

CREATE TABLE with_timestamps(
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE authored(
    author_id BIGINT REFERENCES author(id),
    content text
);


CREATE TABLE post(
    id BIGINT PRIMARY KEY DEFAULT nextval('post_id_sequence'),
    title text
) INHERITS (authored, with_timestamps);


CREATE TABLE comment(
    id BIGINT PRIMARY KEY DEFAULT nextval('comment_id_sequence'),
    post_id BIGINT REFERENCES post(id)
) INHERITS (authored, with_timestamps);
