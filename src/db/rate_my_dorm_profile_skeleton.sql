DROP TABLE Users;
CREATE TABLE Users (
    username varchar(255) NOT NULL,
    email varchar(255) NOT NULL,
    password varchar(255) NOT NULL,
    PRIMARY KEY (username)
);

DROP TABLE Posts;
CREATE TABLE Posts (
    postid int NOT NULL,
    username varchar(256) NOT NULL,
    caption varchar(511),
    description varchar(2047),
    postdate date NOT NULL,
    posttime time NOT NULL,
    PRIMARY KEY (postid)
);

DROP TABLE Comments;
CREATE TABLE Comments (
    commentid int NOT NULL,
    username varchar(255) NOT NULL,
    postid int NOT NULL,
    text varchar(2047) NOT NULL,
    commentdate date NOT NULL,
    commenttime time NOT NULL,
    replytocommentid int,
    PRIMARY KEY (commentid)
);

DROP TABLE Ratings;
CREATE TABLE Ratings (
    username varchar(255) NOT NULL,
    postid int NOT NULL,
    ratingvalue int,
    PRIMARY KEY (username, postid)
);