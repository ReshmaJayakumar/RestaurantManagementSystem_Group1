-- Step 0: Create Database
CREATE DATABASE pRestMgt;
GO

-- Use the newly created database
USE pRestMgt;
GO

-- Step 1: Create Tables

-- Create Users table
CREATE TABLE Users (
    UserID INT PRIMARY KEY IDENTITY(1,1),
    Username NVARCHAR(50) NOT NULL,
    Role NVARCHAR(50) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Create FinancialReports table
CREATE TABLE FinancialReports (
    ReportID INT PRIMARY KEY IDENTITY(1,1),
    Date DATETIME NOT NULL,
    TotalRevenue DECIMAL(10, 2) NOT NULL,
    TotalExpenses DECIMAL(10, 2) NOT NULL,
    NetProfit DECIMAL(10, 2) NOT NULL
);

-- Create PerformanceIndicators table
CREATE TABLE PerformanceIndicators (
    KPIID INT PRIMARY KEY IDENTITY(1,1),
    KPI NVARCHAR(100) NOT NULL,
    Value DECIMAL(10, 2) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Create PerformanceReports table
CREATE TABLE PerformanceReports (
    ReportID INT PRIMARY KEY IDENTITY(1,1),
    Period NVARCHAR(50) NOT NULL,
    KPI NVARCHAR(100) NOT NULL,
    Value DECIMAL(10, 2) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Create Sales table
CREATE TABLE Sales (
    SaleID INT PRIMARY KEY IDENTITY(1,1),
    Item NVARCHAR(100) NOT NULL,
    Quantity INT NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Create CustomerFeedback table
CREATE TABLE CustomerFeedback (
    FeedbackID INT PRIMARY KEY IDENTITY(1,1),
    Feedback NVARCHAR(255) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Create Promotions table
CREATE TABLE Promotions (
    PromoID INT PRIMARY KEY IDENTITY(1,1),
    PromoCode NVARCHAR(50) NOT NULL,
    Discount DECIMAL(5, 2) NOT NULL,
    ExpiryDate DATETIME NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Create ComplianceDocuments table
CREATE TABLE ComplianceDocuments (
    DocumentID INT PRIMARY KEY IDENTITY(1,1),
    DocumentName NVARCHAR(100) NOT NULL,
    DocumentType NVARCHAR(50) NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Create ComplianceDeadlines table
CREATE TABLE ComplianceDeadlines (
    DeadlineID INT PRIMARY KEY IDENTITY(1,1),
    ComplianceType NVARCHAR(100) NOT NULL,
    Deadline DATETIME NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Step 2: Insert Sample Data

-- Insert users
INSERT INTO Users (Username, Role) VALUES ('owner', 'owner'), ('employee1', 'employee'), ('manager1', 'manager');

-- Insert financial reports
INSERT INTO FinancialReports (Date, TotalRevenue, TotalExpenses, NetProfit)
VALUES 
(GETDATE(), 10000, 8000, 2000),
(GETDATE()-1, 11000, 7500, 3500);

-- Insert performance indicators
INSERT INTO PerformanceIndicators (KPI, Value) VALUES ('Customer Satisfaction', 85), ('Employee Efficiency', 90);

-- Insert performance reports
INSERT INTO PerformanceReports (Period, KPI, Value) VALUES ('Weekdays', 'Customer Satisfaction', 85), ('Weekends', 'Customer Satisfaction', 88);

-- Insert sales data
INSERT INTO Sales (Item, Quantity) VALUES ('Burger', 150), ('Pizza', 100);

-- Insert customer feedback
INSERT INTO CustomerFeedback (Feedback) VALUES ('Great service!'), ('Excellent food!');

-- Insert promotions
INSERT INTO Promotions (PromoCode, Discount, ExpiryDate) VALUES ('DISCOUNT10', 10, '2024-12-31');

-- Insert compliance documents
INSERT INTO ComplianceDocuments (DocumentName, DocumentType) VALUES ('Health and Safety Regulations', 'Health and Safety');

-- Insert compliance deadlines
INSERT INTO ComplianceDeadlines (ComplianceType, Deadline) VALUES ('Annual Audit', '2024-12-31');

-- Step 3: SQL Queries for Functionalities

-- 1. View & Download Financial Reports
SELECT * FROM FinancialReports WHERE Date >= DATEADD(DAY, -30, GETDATE());

-- 2. Create User
INSERT INTO Users (Username, Role) VALUES ('new_employee', 'employee');

-- 3. Delete User
DELETE FROM Users WHERE Username = 'new_employee';

-- 4. Change User Role
UPDATE Users SET Role = 'manager' WHERE Username = 'employee1';

-- 5. Track Performance
SELECT KPI, Value FROM PerformanceIndicators;

-- 6. Monitor Customer Trends
SELECT TOP 10 Item, SUM(Quantity) AS TotalSold FROM Sales GROUP BY Item ORDER BY TotalSold DESC;

-- 7. Review Customer Feedback
SELECT Feedback, COUNT(*) AS Frequency FROM CustomerFeedback GROUP BY Feedback;

-- 8. Add Promotion
INSERT INTO Promotions (PromoCode, Discount, ExpiryDate) VALUES ('SUMMER20', 20, '2025-06-30');

-- 9. Delete Promotion
DELETE FROM Promotions WHERE PromoCode = 'SUMMER20';

-- 10. Review Compliance Information
SELECT * FROM ComplianceDocuments;

-- 11. Check Compliance Deadlines
SELECT * FROM ComplianceDeadlines WHERE Deadline > GETDATE();
