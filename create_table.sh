mysql -uroot gci -e "
CREATE TABLE beauty_electronics (
    product_id varchar(255) NOT NULL,
    product_nm varchar(255) NOT NULL,
    price float NOT NULL,
    purposes varchar(255) NOT NULL,
    PRIMARY KEY (product_id),
    KEY ids (product_id)
)"
