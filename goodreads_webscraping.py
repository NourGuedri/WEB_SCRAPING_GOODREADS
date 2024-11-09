import requests
from bs4 import BeautifulSoup
from datetime import datetime
import mysql.connector
from time import sleep

# Connect to MySQL database
db = mysql.connector.connect(host="localhost", user="root",database="goodreads")
cursor = db.cursor()

# Create database and tables:
cursor.execute("CREATE DATABASE IF NOT EXISTS goodreads")
cursor.execute("CREATE TABLE IF NOT EXISTS year (id_year INT AUTO_INCREMENT PRIMARY KEY, year INT)")
cursor.execute("CREATE TABLE IF NOT EXISTS category (id_category INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), year_id INT, FOREIGN KEY (year_id) REFERENCES year(id_year))")
cursor.execute("CREATE TABLE IF NOT EXISTS author (id_author INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), description TEXT, count_books INT, followers INT)")
cursor.execute("CREATE TABLE IF NOT EXISTS book (id_book INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255),description TEXT, avg_rating INT(255), ratingCount INT(255), reviewCount INT(255),votes INT,  published DATE, pages VARCHAR(255), format VARCHAR(255), price INT(255),category_id INT, author_id INT, FOREIGN KEY (category_id) REFERENCES category(id_category), FOREIGN KEY (author_id) REFERENCES author(id_author))")

year = [2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023]

def get_categories():
    for y in year:
        # cursor.execute("INSERT INTO year (year) VALUES (%s)", (y,))
        # db.commit()
        cursor.execute("SELECT id_year FROM year WHERE year = %s", (y,))
        year_id = cursor.fetchone()[0]
        # Fetch all rows before executing a new query
        cursor.fetchall()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        url = f"https://www.goodreads.com/choiceawards/best-books-{y}"
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'lxml')
        categories = soup.find_all('div', {'class': 'category clearFix'})
        print(len(categories))
        # for c in range(13,15):
        
        #     category = categories[c] //hethi taamalha kif data theb tkasamha en bloque bech tsobha sinon tekhethha kemla :
        for category in categories:
            title = category.find('h4', class_='category__copy').text.strip()
            cursor.execute("INSERT INTO category (title, year_id) VALUES (%s, %s)", (title, year_id))
            db.commit()
            
            url = f"https://www.goodreads.com{category.find('a')['href']}"
            src = requests.get(url, headers=headers)
            catsoup=BeautifulSoup(src.content, 'lxml')
            nominees = catsoup.find_all('div', {'class': 'inlineblock'})
           
            # nominees = catsoup.find_all('div', {'class': 'inlineblock'})[10:]
            print("-----------------------------------------------------------------------------------------------------------------------")
            print("Category= ",title)
            get_nominees(nominees,year_id,title)





def get_nominees(nominees,year_id,title):
    
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    # Fetch the id of the category from the database
    cursor.execute("SELECT id_category FROM category WHERE title = %s AND year_id = %s", (title, year_id))
    category_id = cursor.fetchall()[0][0]                                                                

    
    for nominee in nominees:
        # Find the book link within the nominee div and extract the href attribute
        book_link = nominee.find('a', class_='pollAnswer__bookLink')
        book_url = "https://www.goodreads.com" + book_link['href']

        # Send a GET request to the book details page
        response = requests.get(book_url, headers=headers)

        book_soup = BeautifulSoup(response.content, 'lxml')

        # Now that we're on the book details page, we can extract the book information
        book_title = book_soup.find('h1', class_='Text Text__title1')
        if book_title:
            book_title = book_title.text.strip()
        else:
            book_title=None
        book_description = book_soup.find('div', class_='DetailsLayoutRightParagraph__widthConstrained')
        if book_description:
            book_description = book_description.text.strip()
        else:
            book_description=None
        book_avg_rating=book_soup.find('div',class_='RatingStatistics__rating')
        if book_avg_rating:
            book_avg_rating=book_avg_rating.text.strip()
        else:
            book_avg_rating=None
        book_ratings_count = book_soup.find('span', {'data-testid': 'ratingsCount'})
        if book_ratings_count:
            book_ratings_count = book_ratings_count.text.strip()
            book_ratings_count = book_ratings_count[:book_ratings_count.find("ratings")-1]
        else:
            book_ratings_count=None
        
        book_reviews_count = book_soup.find('span', {'data-testid': 'reviewsCount'})
        if book_reviews_count:
            book_reviews_count = book_reviews_count.text.strip()
            book_reviews_count = book_reviews_count[:book_reviews_count.find("reviews")-1]
        else:
            book_reviews_count=None
       
        book_votes = nominee.find('strong', class_='uitext result')
        if book_votes:
            book_votes = book_votes.text.strip()
            book_votes = book_votes[:book_votes.find("votes")-1]
        else:
            book_votes=None
       
        kindle_price = book_soup.find('button', class_='Button Button--buy Button--medium Button--block')
        if kindle_price:
            kindle_price = kindle_price.text.strip()
            kindle_price = kindle_price[kindle_price.find("$")+1:]
        else:
            kindle_price=None
       
        book_pages = book_soup.find('div', class_='FeaturedDetails')
        if book_pages:
            book_pages=book_pages.find('p', {'data-testid': 'pagesFormat'})
            book_pages = book_pages.text.strip()
            book_format = book_pages[book_pages.find("pages,")+7:] 
            book_pages=book_pages[:book_pages.find("pages")-1]
        else:
            book_pages=None
       
        # book_publication_info = book_soup.find('div', class_='FeaturedDetails').find('p', {'data-testid': 'publicationInfo'}).text.strip()
        # date_str = book_publication_info[len("First published "):]
        # date = datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
        book_publication_info = book_soup.find('div', class_='FeaturedDetails')
        if book_publication_info:
            book_publication_info = book_publication_info.find('p', {'data-testid': 'publicationInfo'}).text.strip()
            date_str = book_publication_info[len("First published "):]
        else :
            date_str = f"Jan 1, {year}"
        try:
            # Try to parse the date string as '%B %d, %Y'
            date = datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            try:
                # If that fails, try to parse it as '%B, %Y'
                date = datetime.strptime(date_str, "%B, %Y").strftime("%Y-%m")
            except ValueError:
                # If that also fails, log an error message and set date to None
                print(f"Could not parse date string {date_str}")
                date = None
        author_name = book_soup.find('span', {'data-testid': 'name'})
        if author_name:
            author_name = author_name.text.strip()
        else:
            author_name=None
        descriptions = book_soup.find_all('div', class_='DetailsLayoutRightParagraph__widthConstrained')
        author_description = descriptions[1].find('span', {'class':'Formatted'}).text.strip() if len(descriptions) > 1 else None
        author_count_books=book_soup.find_all('span',class_='Text Text__body3 Text__subdued')[1].text.strip()
        if (int(author_count_books[:author_count_books.find("book")-1].replace(",","")) == 1) :
            author_followers=author_count_books[author_count_books.find("book")+6:author_count_books.find("followers")-1]
        else:
            author_followers=author_count_books[author_count_books.find("books")+5:author_count_books.find("followers")-1]

        author_count_books = author_count_books[:author_count_books.find("book")-1].replace(",","")
        
        print("Book = ",book_title)
        cursor.execute("INSERT INTO author (name, description, count_books, followers) VALUES (%s, %s, %s, %s)", (author_name, author_description, author_count_books, author_followers))
        author_id = cursor.lastrowid
        cursor.execute("INSERT INTO book (title, description, avg_rating, ratingCount, reviewCount, votes, published, pages, format, price, category_id, author_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (book_title, book_description, book_avg_rating, book_ratings_count, book_reviews_count, book_votes, date, book_pages, book_format, kindle_price, category_id, author_id))
        db.commit()


def main():

    get_categories()




#Appel de la fonction principale  pour lancer le script
main()