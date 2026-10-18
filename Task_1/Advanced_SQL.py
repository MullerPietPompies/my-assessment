"""
The database loan.db consists of 5 tables:
   1. customers - table containing customer data
   2. loans - table containing loan data pertaining to customers
   3. credit - table containing credit and creditscore data pertaining to customers
   4. repayments - table containing loan repayment data pertaining to customers
   5. months - table containing month name and month ID data

You are required to make use of your knowledge in SQL to query the database object (saved as loan.db) and return the requested information.
Simply fill in the vacant space wrapped in triple quotes per question (each function represents a question)

NOTE:
The database will be reset when grading each section. Any changes made to the database in the previous `SQL` section can be ignored.
Each question in this section is isolated unless it is stated that questions are linked.
Remember to clean your data

"""


def question_1():
    """
    Make use of a JOIN to find the `AverageIncome` per `CustomerClass`
    """
    # In the first section there are duplicates in the customer database that will affect the results therefore I need to filter and find only distinct results in "customers"
    qry = """
        SELECT cr.CustomerClass, AVG(c.Income) as AverageIncome
        FROM (SELECT DISTINCT * FROM customers) c
        INNER JOIN (SELECT DISTINCT * FROM credit) cr
            ON c.CustomerID = cr.CustomerID
        GROUP BY cr.CustomerClass
    """

    return qry


def question_2():
    """
    Make use of a JOIN to return a breakdown of the number of 'RejectedApplications' per 'Province'.
    Ensure consistent use of either the abbreviated or full version of each province, matching the format found in the customer table.
    """
    # Looking at all data in the db I can see some records show the Province (Region) as the Full name with no spaces or the abbreviated version 
    # Looking at the Data 'KwaZulu-Natal' Shows up in the data format differs from the rest therefore I will Unify all to the Full name in the Database following that format (no spaces)
    # Gauteng does not use the sandard GP abbreviation instead uses GT
    # Will have to standardize before processing. 
    qry = """ 
        SELECT Province, COUNT(*) AS RejectedApplications
        FROM (
            SELECT 
                CASE UPPER(TRIM(c.Region))
                    WHEN 'EC' THEN 'EasternCape'
                    WHEN 'GT' THEN 'Gauteng'
                    WHEN 'KZN' THEN 'KwaZulu-Natal'
                    WHEN 'WC' THEN 'WesternCape'
                    WHEN 'LP' THEN 'Limpopo'
                    WHEN 'MP' THEN 'Mpumalanga'
                    WHEN 'NW' THEN 'NorthWest'
                    WHEN 'FS' THEN 'FreeState'
                    WHEN 'NC' THEN 'NorthenCape'
                    ELSE TRIM(c.Region)
                END AS Province
                FROM (SELECT DISTINCT * FROM Customers) c
            INNER JOIN (SELECT DISTINCT * FROM loans) l 
                ON c.CustomerID = l.CustomerID
            -- Making sure the data is clean
            WHERE LOWER(TRIM(ApprovalStatus)) = 'rejected'
            )
            GROUP BY Province
            ORDER BY RejectedApplications DESC
    """

    return qry


def question_3():
    """
    Making use of the `INSERT` function, create a new table called `financing` which will include the following columns:
    `CustomerID`,`Income`,`LoanAmount`,`LoanTerm`,`InterestRate`,`ApprovalStatus` and `CreditScore`

    Do not return the new table, just create it.
    """

    qry = """
        CREATE TABLE financing (
            -- Most numeric fields (except 'InterestRate') are stored as INTEGER in the original DB, I will stick to that Data Type
            CustomerID  INTEGER,
            Income      INTEGER,
            LoanAmount  INTEGER,
            LoanTerm    INTEGER,
            InterestRate    FLOAT,
            ApprovalStatus  VARCHAR,
            CreditScore     INTEGER 
        );

        INSERT INTO financing (CustomerID, Income, LoanAmount, LoanTerm, InterestRate, ApprovalStatus, CreditScore)
            SELECT c.CustomerID, c.Income, l.LoanAmount, l.LoanTerm, l.InterestRate, l.ApprovalStatus, cr.CreditScore
            FROM (SELECT DISTINCT * FROM customers) c
            INNER JOIN (SELECT DISTINCT * FROM loans) l
                ON c.CustomerID = l.CustomerID
            INNER JOIN (SELECT DISTINCT * FROM credit) cr
                ON c.CustomerID = cr.CustomerID

    """

    return qry


# Question 4 and 5 are linked


def question_4():
    """
    Using a `CROSS JOIN` and the `months` table, create a new table called `timeline` that sumarises Repayments per customer per month.
    Columns should be: `CustomerID`, `MonthName`, `NumberOfRepayments`, `AmountTotal`.
    Repayments should only occur between 6am and 6pm London Time.
    Null values to be filled with 0.

    Hint: there should be 12x CustomerID = 1.
    """

    qry = """
    CREATE TABLE timeline(
        CustomerID  INTEGER,
        MonthName   VARCHAR,
        NumberOfRepayments   INTEGER,
        AmountTotal INTEGER
    );
    
    INSERT INTO timeline (CustomerID, MonthName, NumberOfRepayments, AmountTotal)
    SELECT
        c.CustomerID, 
        m.MonthName,
        COUNT(r.CustomerID) AS NumberOfRepayments,
        -- Use COALESCE to fill the null values with 0
        COALESCE(SUM(r.Amount),0) AS AmountTotal
    FROM (SELECT DISTINCT CustomerID FROM customers) c
    CROSS JOIN months m
    LEFT JOIN (
        -- The London Time Zone and 6am-6pm Filter
        -- I need to convert all times to london time to get the actual repayments regardless of time zone in London time to see if they land inbetween the 6am and 6pm range
        -- The RepaymentDate is a tiemstamp making the filtering easier using the TIME() function to isolate the time from the timestamp
        SELECT CustomerID, Amount, LondonTime
        FROM (SELECT 
        CustomerID,
        Amount,
        timezone('Europe/London', timezone('UTC',
            RepaymentDate - to_minutes(
            -- Since IST is used in the db '+5:30' from UTC to_hours will not work since it only takes whole numbers
            -- The offset for each timezone will be calculated in minutes to get the UTC time that the repayment happened
            -- Only using the timezones listed in the DB
                CASE UPPER(TRIM(TimeZone))
                    WHEN 'UTC' THEN 0
                    WHEN 'GMT' THEN 0 
                    WHEN 'IST' THEN 330
                    WHEN 'PST' THEN -480
                    WHEN 'JST' THEN 540
                    WHEN 'EET' THEN 120
                    WHEN 'PNT' THEN -420
                    WHEN 'CST' THEN -360
                    WHEN 'CET' THEN 60
                END
            ) 
        )) AS LondonTime
        FROM (SELECT DISTINCT * FROM repayments)
        )
        WHERE CAST(LondonTime AS TIME) BETWEEN TIME '06:00:00' AND '18:00:00'
    ) r
    ON r.CustomerID = c.CustomerID
    AND month(r.LondonTime) = m.MonthID
    GROUP BY c.CustomerID, m.MonthID, m.MonthName
    ORDER BY c.CustomerID, m.MonthID
    """

    return qry


def question_5():
    """
    Make use of conditional aggregation to pivot the `timeline` table such that the columns are as follows:
    `CustomerID`, `JanuaryRepayments`, `JanuaryTotal`,...,`DecemberRepayments`, `DecemberTotal`,...etc
    MonthRepayments columns (e.g JanuaryRepayments) should be integers

    Hint: there should be 1x CustomerID = 1
    """

    qry = """
    -- Will have to do each month manually to map them
    SELECT CustomerID, 

    CAST(SUM(CASE WHEN MonthName = 'January' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS JanuaryRepayments,
    SUM(CASE WHEN MonthName = 'January' THEN AmountTotal ELSE 0 END) AS JanuaryTotal,

    CAST(SUM(CASE WHEN MonthName = 'February' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS FebruaryRepayments,
    SUM(CASE WHEN MonthName = 'February' THEN AmountTotal ELSE 0 END) AS FebruaryTotal,

    CAST(SUM(CASE WHEN MonthName = 'March' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS MarchRepayments,
    SUM(CASE WHEN MonthName = 'March' THEN AmountTotal ELSE 0 END) AS MarchTotal,

    CAST(SUM(CASE WHEN MonthName = 'April' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS AprilRepayments,
    SUM(CASE WHEN MonthName = 'April' THEN AmountTotal ELSE 0 END) AS AprilTotal,

    CAST(SUM(CASE WHEN MonthName = 'May' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS MayRepayments,
    SUM(CASE WHEN MonthName = 'May' THEN AmountTotal ELSE 0 END) AS MayTotal,

    CAST(SUM(CASE WHEN MonthName = 'June' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS JuneRepayments,
    SUM(CASE WHEN MonthName = 'June' THEN AmountTotal ELSE 0 END) AS JuneTotal,

    CAST(SUM(CASE WHEN MonthName = 'July' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS JulyRepayments,
    SUM(CASE WHEN MonthName = 'July' THEN AmountTotal ELSE 0 END) AS JulyTotal,

    CAST(SUM(CASE WHEN MonthName = 'August' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS AugustRepayments,
    SUM(CASE WHEN MonthName = 'August' THEN AmountTotal ELSE 0 END) AS AugustTotal,

    CAST(SUM(CASE WHEN MonthName = 'September' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS SeptemberRepayments,
    SUM(CASE WHEN MonthName = 'September' THEN AmountTotal ELSE 0 END) AS SeptemberTotal,

    CAST(SUM(CASE WHEN MonthName = 'October' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS OctoberRepayments,
    SUM(CASE WHEN MonthName = 'October' THEN AmountTotal ELSE 0 END) AS OctoberTotal,

    CAST(SUM(CASE WHEN MonthName = 'November' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS NovemberRepayments,
    SUM(CASE WHEN MonthName = 'November' THEN AmountTotal ELSE 0 END) AS NovemberTotal,

    CAST(SUM(CASE WHEN MonthName = 'December' THEN NumberOfRepayments ELSE 0 END) AS INTEGER) AS DecemberRepayments,
    SUM(CASE WHEN MonthName = 'December' THEN AmountTotal ELSE 0 END) AS DecemberTotal

    FROM timeline
    GROUP BY CustomerID   
    ORDER BY CustomerID
    """

    return qry


# QUESTION 6 and 7 are linked, Do not be concerned with timezones or repayment times for these question.


def question_6():
    """
    The `customers` table was created by merging two separate tables: one containing data for male customers and the other for female customers.
    Due to an error, the data in the age columns were misaligned in both original tables, resulting in a shift of two places upwards in
    relation to the corresponding CustomerID.

    Create a table called `corrected_customers` with columns: `CustomerID`, `Age`, `CorrectedAge`, `Gender`
    Utilize a window function to correct this mistake in the new `CorrectedAge` column.
    Null values can be input manually - i.e. values that overflow should loop to the top of each gender.

    Also return a result set for this table (ie SELECT * FROM corrected_customers)
    """

    qry = """
    CREATE TABLE corrected_customers AS 
    WITH clean AS (
    -- Remove Duplicates to ensure the shift is ready
        SELECT DISTINCT CustomerID, Age, TRIM(Gender) AS Gender
        FROM customers
    ), 
    numbered AS (
        SELECT 
            CustomerID, 
            Age, 
            Gender,
            ROW_NUMBER() OVER (PARTITION BY Gender ORDER BY CustomerID) AS rn,
            COUNT(*) OVER (PARTITION BY Gender) AS cnt
        FROM clean
    )

    SELECT 
        n.CustomerID,
        n.Age,
        CASE
            -- Case when overflow and then wrap to the top: Take the last 2 values of each gender 
            WHEN n.rn<= 2 THEN (
                SELECT n2.Age FROM numbered n2
                WHERE n2.Gender = n.Gender
                    AND n2.rn = n.cnt - 2 + n.rn
            )
        ELSE LAG(n.Age, 2) OVER (PARTITION BY n.Gender ORDER BY n.CustomerID)
        END AS CorrectedAge, n.Gender
        FROM numbered n
        ORDER BY n.CustomerID;

        SELECT * FROM corrected_customers;
    """

    return qry


def question_7():
    """
    Create a column in corrected_customers called 'AgeCategory' that categorizes customers by age.
    Age categories should be as follows:
        - `Teen`: CorrectedAge < 20
        - `Young Adult`: 20 <= CorrectedAge < 30
        - `Adult`: 30 <= CorrectedAge < 60
        - `Pensioner`: CorrectedAge >= 60

    Make use of a windows function to assign a rank to each customer based on the total number of repayments per age group. Add this into a "Rank" column.
    The ranking should not skip numbers in the sequence, even when there are ties, i.e. 1,2,2,2,3,4 not 1,2,2,2,5,6
    Customers with no repayments should be included as 0 in the result.

    Return columns: `CustomerID`, `Age`, `CorrectedAge`, `Gender`, `AgeCategory`, `Rank`
    """

    qry = """
    ALTER TABLE corrected_customers ADD COLUMN AgeCategory VARCHAR;

    UPDATE corrected_customers 
    SET AgeCategory = CASE 
        WHEN CorrectedAge < 20 THEN 'Teen' 
        WHEN CorrectedAge < 20 THEN 'Young Adult'
        WHEN CorrectedAge < 60 THEN 'Adult'
        WHEN CorrectedAGE >= 60 THEN 'Pensioner'
    END;
    
    SELECT c.CustomerID, c.Age, c.CorrectedAge, c.Gender, c.AgeCategory, 
    -- Ranking 
    DENSE_RANK() OVER (PARTITION BY c.AgeCategory ORDER BY COALESCE(r.TotalRepayments, 0) DESC) AS "Rank"
    FROM corrected_customers c
    LEFT JOIN (
        SELECT CustomerID, COUNT(*) AS TotalRepayments
        FROM (SELECT DISTINCT * FROM repayments)
        GROUP BY CustomerID 
    ) r
    
        ON c.CustomerID = r.CustomerID
    ORDER BY c.AgeCategory, "Rank";

"""

    return qry
