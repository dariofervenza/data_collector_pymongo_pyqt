# Changelog

## v0.2.2

### Added
- New application diagram. Now you could check how I deployed my application on my Windows pc (Docker implementation not available for now)
- Remade readme.md with better explanations and new images

## 2023-27-12
- Improved client auth widget: Now it asks the server address and it sends messages if there is an error
- Improved client alarms widget: Added a field where you can introduce the date after which you can display the notifications

## 2023-28-12:
- Added forecasting single series widget (client)

## 2023-29-12:
- Added backtesting single series widget (client)

## 2024-14-01:
- Changed design to fluent design (not finished yet though)
- Redesigned Graphs widget - now you can add, remove and resize plots
- Solved a bug where you couldn't move the vertical scroll bar

## 2024-21-01:
- Switched to weatherapi.com API
- Continued implementing fluentDesign (not finished)
- More UI changes

## 2024-11-02:
- Patched some bugs
- Improved UI
- Added dotenv to protect the secret key
- Added rabitMQ to decouple api response from the server
- Now the analytics figures are stored in a redis db
- Now alarm notifications are created when the data is added to the db
- Some other minor changes

## 2024-18-02:
- Added filter functions to graphs widget
- Improved code with pylint
- Added MIT license

