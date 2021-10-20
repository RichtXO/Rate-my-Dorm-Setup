CREATE TABLE IF NOT EXISTS Users (
    username varchar(255) NOT NULL UNIQUE,
    email varchar(255) NOT NULL UNIQUE,
    password varchar(255) NOT NULL,
    PRIMARY KEY (username)
);

CREATE TABLE IF NOT EXISTS Follows(
    follower varchar(255) NOT NULL,
    follows varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Posts (
    postid bigint NOT NULL,
    username varchar(256) NOT NULL,
    caption varchar(511),
    description varchar(2047),
    postdate date NOT NULL,
    posttime time NOT NULL,
    PRIMARY KEY (postid)
);

CREATE TABLE IF NOT EXISTS Comments (
    commentid bigint NOT NULL,
    username varchar(255) NOT NULL,
    postid bigint NOT NULL,
    text varchar(2047) NOT NULL,
    commentdate date NOT NULL,
    commenttime time NOT NULL,
    replytocommentid int,
    PRIMARY KEY (commentid)
);

CREATE TABLE IF NOT EXISTS Ratings (
    username varchar(255) NOT NULL,
    postid bigint NOT NULL,
    ratingvalue int,
    PRIMARY KEY (username, postid)
);
