DROP TABLE IF EXISTS rooms;
CREATE TABLE rooms (
       id INT NOT NULL AUTO_INCREMENT,
       jid VARCHAR(255),
       name VARCHAR(255),
       PRIMARY KEY (id)
) ENGINE = INNODB;

DROP TABLE IF EXISTS messages;
CREATE TABLE messages (
       id INT NOT NULL AUTO_INCREMENT,
       room_id INT NOT NULL,
       speaker VARCHAR(255) NOT NULL,
       message TEXT,
       created_at DATETIME,
       PRIMARY KEY (id)
) ENGINE = INNODB;
