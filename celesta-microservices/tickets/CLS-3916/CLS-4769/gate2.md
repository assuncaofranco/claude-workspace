# CLS-4769 gate 2

## 1. Implementation commit
Branch `CLS-4769`, worktree `/private/tmp/cls3916/celesta-activity`. History on top of the plan commit:
`32a9d1ee CLS-4769 plan` -> `ed19a91b CLS-4769 Merge master into CLS-4769` -> **`90e11751 CLS-4769 Accept the promotion source type in the activity filters`**.
Not pushed.

`git diff --stat ed19a91b 90e11751`:

```
 database/mongo/fixtures/user_activity.yml         |  34 ++++++
 internal/api/user_activity_handler.go             |   2 +-
 internal/api/v1/user_activity.go                  |   2 +-
 internal/pkg/constants/user_activity.go           |   2 +
 test/intergration/api_user_activity_test.go       | 121 ++++++++++++++++++++++
 test/intergration/messeging_user_activity_test.go |  54 ++++++++++
 6 files changed, 213 insertions(+), 2 deletions(-)
```

## 2. Tasks and criteria

| Task | Where | Test that covers it |
|---|---|---|
| 1 const | `internal/pkg/constants/user_activity.go:301` | filter cases below (the validator reads `AllSourceTypes`) |
| 2 `AllSourceTypes` | `internal/pkg/constants/user_activity.go:313` | "Get the entries of the promotion source type"; fails with 400 without it |
| 3 swagger Enums | `internal/api/user_activity_handler.go:39` | manual `make openapi` check (section 3) |
| 4 `Items Enum:` comment | `internal/api/v1/user_activity.go:46` | none (comment) |
| 5 fixtures | `database/mongo/fixtures/user_activity.yml:574` and `:591` | the API cases below |
| 6 messaging subtest | `test/intergration/messeging_user_activity_test.go:1094` | itself: `TestMessaging_UserActivity/Must_keep_the_payload_of_a_gift_offered_promotion_event` |
| 7 one promotion | `test/intergration/api_user_activity_test.go:668` | itself |
| 8 all promotion entries | `test/intergration/api_user_activity_test.go:703` | itself |
| 9 one player | `test/intergration/api_user_activity_test.go:732` | itself |
| 10 unknown type rejected | `test/intergration/api_user_activity_test.go:754` | itself |
| 11 aggregate | `test/intergration/api_user_activity_test.go:1092` | itself |
| 12 run Testing Strategy | section 3 | |

| Acceptance criterion | Met by |
|---|---|
| `gift_offered` with `source_type: promotion` stored as sent | messaging subtest (task 6), asserts type, id, player, domain, payload |
| `filter[sourceTypes]=promotion` returns the entries; with `sourceIds` that promotion's only | tasks 8 and 7 |
| `filter[event]=gift_offered` + `playerIds` returns the player's entry | task 9 |
| aggregate with `sourceTypes: ["promotion"]` returns 200 and the count | task 11 (2) |
| unknown source type returns 400 | task 10 |
| `promotion` in the OpenAPI enum | `make openapi`: `filter[sourceTypes]` items enum = player, system, application, company, user, seon, scenario, fraud, promotion |

Not exercised: the "fails without the change" claim for the filter cases was not re-run on master (the branch is the
only build in the container).

## 3. Commands and output

Environment: image `.../celesta/activity:latest-dev` rebuilt by Lucas, `go version go1.27.3 linux/arm64`.
`GITHUB_ACCESS_TOKEN=$(gh auth token) make init` exit 0 (fixtures loaded in `activity` and `activity_test`, `make openapi`
generated `public/assets/swagger.json`, git-ignored).

### `docker compose -f docker-compose.dev.yml exec -T api go test ./test/intergration/ -run 'TestMessaging_UserActivity|TestGetUserActivities' -v -count=1` (exit 0; 66 PASS, 0 FAIL; lines of results, debug logs omitted)
```
--- PASS: TestGetUserActivities (0.03s)
    --- PASS: TestGetUserActivities/Get_user_activities_by_filters,_orderBy_and_limit (0.00s)
    --- PASS: TestGetUserActivities/Validation_errors (0.00s)
    --- PASS: TestGetUserActivities/Get_auto_withdrawal_reserved_amount_changed_user_activities (0.00s)
    --- PASS: TestGetUserActivities/Get_iban_match_user_activities_filtered_by_the_fraud_source_type (0.00s)
    --- PASS: TestGetUserActivities/Get_run_fraud_rule_user_activities_filtered_by_the_scenario_source_type (0.00s)
    --- PASS: TestGetUserActivities/Get_scenario_reward_offered_user_activities,_bonus_and_gift (0.00s)
    --- PASS: TestGetUserActivities/Get_scenario_reward_offer_skipped_user_activities,_bonus_and_gift (0.00s)
    --- PASS: TestGetUserActivities/Get_the_update_player_tag_entries_of_one_scenario (0.00s)
    --- PASS: TestGetUserActivities/Get_the_update_player_tag_entries_of_one_player (0.00s)
    --- PASS: TestGetUserActivities/Get_the_gift_request_entries_of_one_player (0.00s)
    --- PASS: TestGetUserActivities/Get_the_gift_requested_entries_requested_from_the_Backoffice_in_one_domain (0.00s)
    --- PASS: TestGetUserActivities/Reject_the_gift_request_approved_event_in_the_filter (0.00s)
    --- PASS: TestGetUserActivities/Get_the_gift_offered_entries_of_one_player (0.00s)
    --- PASS: TestGetUserActivities/Get_the_gift_offered_entries_offered_from_the_Backoffice_in_one_domain (0.00s)
    --- PASS: TestGetUserActivities/Reject_the_gift_claimed_event_in_the_filter (0.00s)
    --- PASS: TestGetUserActivities/Get_the_department_events_of_one_Backoffice_user (0.00s)
    --- PASS: TestGetUserActivities/Get_the_gift_offered_entries_of_one_promotion (0.00s)
    --- PASS: TestGetUserActivities/Get_the_entries_of_the_promotion_source_type (0.00s)
    --- PASS: TestGetUserActivities/Get_the_promotion_gift_offered_entries_of_one_player (0.00s)
    --- PASS: TestGetUserActivities/Reject_an_unknown_source_type_in_the_filter (0.00s)
--- PASS: TestGetUserActivitiesByCompanyID (0.01s)
    --- PASS: TestGetUserActivitiesByCompanyID/Filter_by_companyIds_returns_matching_activities (0.00s)
    --- PASS: TestGetUserActivitiesByCompanyID/Filter_by_multiple_companyIds (0.00s)
    --- PASS: TestGetUserActivitiesByCompanyID/Sort_by_companyId_ascending (0.00s)
--- PASS: TestGetUserActivitiesForCelestaUser (0.00s)
    --- PASS: TestGetUserActivitiesForCelestaUser/Logs_tab_query_returns_all_events_of_the_Celesta_User (0.00s)
--- PASS: TestGetUserActivitiesAggregate (0.04s)
    --- PASS: TestGetUserActivitiesAggregate/Get_user_activities_by_filters,_groupBy_and_aggregations (0.02s)
    --- PASS: TestGetUserActivitiesAggregate/Get_user_activities_by_filters_and_aggregations (0.00s)
    --- PASS: TestGetUserActivitiesAggregate/Group_by_companyId (0.00s)
    --- PASS: TestGetUserActivitiesAggregate/Count_Celesta_User_log_events (0.00s)
    --- PASS: TestGetUserActivitiesAggregate/Count_run_fraud_rule_scenario_log_events (0.00s)
    --- PASS: TestGetUserActivitiesAggregate/Count_update_player_tag_scenario_log_events (0.00s)
    --- PASS: TestGetUserActivitiesAggregate/Count_gift_offered_Backoffice_log_events (0.00s)
    --- PASS: TestGetUserActivitiesAggregate/Count_gift_request_Backoffice_log_events (0.00s)
    --- PASS: TestGetUserActivitiesAggregate/Count_department_events_of_one_Backoffice_user (0.00s)
    --- PASS: TestGetUserActivitiesAggregate/Count_gift_offered_promotion_log_events (0.00s)
--- PASS: TestMessaging_UserActivity (0.05s)
    --- PASS: TestMessaging_UserActivity/Must_create_2_documents_with_chunked_player_IDs (0.01s)
    --- PASS: TestMessaging_UserActivity/Must_create_document_for_system_user_ (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_handle_player_ids_as_slice_of_strings (0.01s)
    --- PASS: TestMessaging_UserActivity/Must_handle_player_ids_as_slice_of_mixed_types (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_handle_single_player_id_as_string (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_handle_single_player_id_as_float (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_handle_player_ids_with_invalid_strings_gracefully (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_handle_empty_player_ids_slice (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_prioritize_player_ids_over_player_id_when_both_present (0.01s)
    --- PASS: TestMessaging_UserActivity/Must_extract_company_id_from_additional_data_as_int (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_extract_company_id_from_additional_data_as_float64 (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_extract_company_id_from_additional_data_as_string (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_handle_missing_company_id_gracefully (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_process_with_special_chars (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_an_iban_match_fraud_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_a_reward_offered_scenario_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_a_reward_offer_skipped_scenario_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_additional_data_for_segment_preview (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_a_run_fraud_rule_scenario_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_error_payload_of_a_run_fraud_rule_scenario_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_an_update_player_tag_scenario_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_a_gift_offered_Backoffice_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_a_gift_requested_Backoffice_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_a_gift_request_rejected_Backoffice_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_a_department_updated_Backoffice_event (0.00s)
    --- PASS: TestMessaging_UserActivity/Must_keep_the_payload_of_a_gift_offered_promotion_event (0.00s)
--- PASS: TestMessaging_UserActivity_FlushesWhenTheBufferIsFull (0.02s)
PASS
ok  	github.com/celesta-tech/celesta-activity/test/intergration	0.162s
```

### `make test` (exit 0)
```
ok  	github.com/celesta-tech/celesta-activity/internal/api	0.077s	coverage: 79.5% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/api/v1	0.005s	coverage: 100.0% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/bootstrap	0.029s	coverage: 39.6% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/command	0.092s	coverage: 100.0% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/dto/dto	0.009s	coverage: 100.0% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/dto/model	0.017s	coverage: 100.0% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/health	0.112s	coverage: 89.7% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/messaging	0.047s	coverage: 93.6% of statements
?   	github.com/celesta-tech/celesta-activity/internal/pkg/constants	[no test files]
ok  	github.com/celesta-tech/celesta-activity/internal/pkg/validator	0.008s	coverage: 88.2% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/pkg/validator/validation	0.004s	coverage: 100.0% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/pkg/whitelist	0.029s	coverage: 100.0% of statements
ok  	github.com/celesta-tech/celesta-activity/internal/repository	0.003s	coverage: 25.8% of statements
?   	github.com/celesta-tech/celesta-activity/public	[no test files]
ok  	github.com/celesta-tech/celesta-activity/test/intergration	0.236s	coverage: [no statements]
```

### `make lint` (exit 0)
```
docker compose -f docker-compose.dev.yml exec api bash -c 'GOFLAGS=-buildvcs=false golangci-lint run ./...'
time="2026-11-17T15:32:54Z" level=warning msg="The \"GITHUB_ACCESS_TOKEN\" variable is not set. Defaulting to a blank string."
0 issues.
```

## 4. Deviations
- Fixture `_id`s are quoted strings, like the existing gift fixtures.
- Merge: the branch was 14 commits behind origin/master (CLS-4302, CLS-4541). Merged as ordered
  (`ed19a91b`, no conflicts). Re-applying my work with `git apply --3way` conflicted in the fixtures and both test files
  (both sides appended at the same spot, in `TestGetUserActivities` and `TestGetUserActivitiesAggregate` tables too).
  Resolution: reset those 3 files to the merge result and re-inserted my blocks after master's, keeping all cases of
  both sides, mechanically, no logic touched. The 3 other files applied cleanly. No duplicate `_id`; players
  791101/791102 and source ids 7301/7302 only appear in my fixtures.
- `make build` fails on master (Dockerfile reads the token as a BuildKit secret, `docker-compose.dev.yml` passes an arg):
  not worked around, Lucas rebuilt the image.
- Proteus repo: added a short `_plans/activity/CLS-4769.md` that the plan did not list, next to the spec the plan asks for.
- Qase dry run (`npm run qase:sync`) not run: no Qase credential. The spec lists the four steps under Qase pending.

## 5. Proteus
Worktree `/private/tmp/cls3916/celesta-qaa-proteus-4769`, branch `CLS-4769`, commit **`b7d084252`**
(`CLS-4769 Filter the user activities by the promotion source type`), not pushed, not run (service CI validates).

```
 _plans/activity/CLS-4769.md                        | 20 +++++++++
 _specs/activity/CLS-4769.md                        | 47 ++++++++++++++++++++++
 src/data-services/types/constants.ts               |  1 +
 .../service/userActivitiesFilters.pca-4.test.ts    | 42 +++++++++++++++++++
```
`npx tsc --noEmit` and eslint on the two code files: clean.

Attribution grep (`git log origin/master..HEAD --format='%s%n%b' | grep -iE 'co-authored|🤖|generated with|claude code'`)
printed nothing in both worktrees.
