# Feature: Gemini Analytics API
- Scenario: Check the 'readiness' REST API point for the Gemini service
- Scenario: Check the 'liveness' REST API point for the Gemini service
- Scenario Outline: Check that the HTTP method is check properly on Gemini side for the /api/v1/readiness endpoint
- Scenario: Check that the HTTP method is check properly on Gemini side for the /api/v1/readiness endpoint
- Scenario Outline: Check that the HTTP method is check properly on Gemini side for the /api/v1/liveness endpoint
- Scenario: Check that the HTTP method is check properly on Gemini side for the /api/v1/liveness endpoint
- Scenario: Check the 'readiness' REST API point for the Gemini service with using authorization token
- Scenario: Check the 'liveness' REST API entry point for the Gemini service with using authorization token
- Scenario: Check the Gemini API /api/v1/register response
- Scenario: Gemini /api/v1/report check when called without arguments and without authorization token
- Scenario: Gemini /api/v1/report check when called without arguments but with authorization token
- Scenario: Check the Gemini API /api/v1/report response, basic test
- Scenario: Check the Gemini API /api/v1/report response, complete test
- Scenario: Check the Gemini API /api/v1/user-repo/notify response
- Scenario: Check the Gemini API /api/v1/user-repo/drop
- Scenario: Check that the 'register' REST API point for the Gemini service accepts POST method only
- Scenario: Check that the 'user-repo/scan' REST API point for the Gemini service accepts POST method only
- Scenario: Check that the 'user-repo/notify' REST API point for the Gemini service accepts POST method only
- Scenario: Check that the 'user-repo/drop' REST API point for the Gemini service accepts POST method only
- Scenario: Check the Gemini API endpoint 'stacks-report/list' for daily report list
- Scenario: Check the Gemini API endpoint 'stacks-report/list' for weekly report list
- Scenario: Check the Gemini API endpoint 'stacks-report/list' for monthly report list
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for selected daily report
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for selected weekly report
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for selected monthly report
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for daily report - the first daily report
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for weekly report - the first weekly report
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for monthly report - the first monthly report
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for daily report - the last daily report
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for weekly report - the last weekly report
- Scenario: Check the Gemini API endpoint 'stacks-report/report' for monthly report - the last monthly report
