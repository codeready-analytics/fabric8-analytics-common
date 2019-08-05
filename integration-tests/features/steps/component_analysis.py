"""Tests for API endpoints that performs component search and component analysis."""
import requests

import time

from behave import given, then, when
from urllib.parse import urljoin

from src.parsing import parse_token_clause
from src.utils import split_comma_separated_list
from src.json_utils import get_value_using_path
from src.authorization_tokens import authorization
from src.attribute_checks import check_attribute_presence, check_cve_value


@given('Component search service is running')
def running_component_search_api(context):
    """Wait for the component search REST API to be available."""
    if not context.is_component_search_service_running(context):
        context.wait_for_component_search_service(context, 60)


def component_analysis_url(context, ecosystem, component, version):
    """Construct URL for the component analyses REST API call."""
    return urljoin(context.coreapi_url,
                   'api/v1/component-analyses/{e}/{c}/{v}'.format(e=ecosystem,
                                                                  c=component,
                                                                  v=version))


def context_reponse_existence_check(context):
    """Preliminary check if the context.response exists."""
    assert context is not None
    assert context.response is not None


def perform_component_search(context, component, use_token):
    """Call API endpoint to search for component."""
    path = "api/v1/component-search/{component}".format(component=component)
    url = urljoin(context.coreapi_url, path)
    if use_token:
        context.response = requests.get(url, headers=authorization(context))
    else:
        context.response = requests.get(url)


@when("I search for component {component} without authorization token")
def search_for_component_without_token(context, component):
    """Search for given component via the component search REST API call."""
    perform_component_search(context, component, False)


@when("I search for component {component} with authorization token")
def search_for_component_with_token(context, component):
    """Search for given component via the component search REST API call."""
    perform_component_search(context, component, True)


@when("I read {ecosystem}/{component}/{version} component analysis")
@when("I read {ecosystem}/{component}/{version} component analysis "
      "{token} authorization token")
def read_analysis_for_component(context, ecosystem, component, version, token='without'):
    """Read component analysis (or an error message) for the selected ecosystem."""
    context.duration = None
    start_time = time.time()

    url = component_analysis_url(context, ecosystem, component, version)

    use_token = parse_token_clause(token)

    if use_token:
        context.response = requests.get(url, headers=authorization(context))
    else:
        context.response = requests.get(url)
    end_time = time.time()
    # compute the duration
    # plase note that duration==None in case of any errors (which is to be expected)
    context.duration = end_time - start_time


@when("I start analysis for component {ecosystem}/{component}/{version}")
@when("I start analysis for component {ecosystem}/{component}/{version} "
      "{token} authorization token")
def start_analysis_for_component(context, ecosystem, component, version, token='without'):
    """Start the component analysis.

    Start the analysis for given component and version in selected ecosystem.
    Current API implementation returns several HTTP codes:
    200 OK : analysis is already finished
    202 ACCEPTED: analysis is not finished, might be planned (or not)
    400 BAD REQUST: unknown ecosystem etc. etc.
    401 UNAUTHORIZED : missing or inproper authorization token
    404 NOT FOUND : analysis is started or is in progress
    It means that this test step should check if 200 OK is NOT returned.
    """
    url = component_analysis_url(context, ecosystem, component, version)

    use_token = parse_token_clause(token)

    # first check that the analysis is really new
    if use_token:
        response = requests.get(url, headers=authorization(context))
    else:
        response = requests.get(url)

    # remember the response for further test steps
    context.response = response

    if response.status_code == 200:
        raise Exception('Bad state: the analysis for component has been '
                        'finished already')
    elif response.status_code not in (202, 400, 401, 404):
        raise Exception('Improper response: expected HTTP status code 401 or 404, '
                        'received {c}'.format(c=response.status_code))


@when("I wait for {ecosystem}/{component}/{version} component analysis to finish")
@when("I wait for {ecosystem}/{component}/{version} component analysis to finish "
      "{token} authorization token")
def finish_analysis_for_component(context, ecosystem, component, version, token='without'):
    """Try to wait for the component analysis to be finished.

    Current API implementation returns just two HTTP codes:
    200 OK : analysis is already finished
    404 NOT FOUND: analysis is started or is in progress
    """
    timeout = context.component_analysis_timeout  # in seconds
    sleep_amount = 10  # we don't have to overload the API with too many calls

    use_token = parse_token_clause(token)

    url = component_analysis_url(context, ecosystem, component, version)

    for _ in range(timeout // sleep_amount):
        if use_token:
            status_code = requests.get(url, headers=authorization(context)).status_code
        else:
            status_code = requests.get(url).status_code
        if status_code == 200:
            break
        elif status_code != 404:
            raise Exception('Bad HTTP status code {c}'.format(c=status_code))
        time.sleep(sleep_amount)
    else:
        raise Exception('Timeout waiting for the component analysis results')


@when('I look at recent component analysis')
def look_at_recent_component_analysis(context):
    """Just dummy step to make test scenarios more readable."""
    assert context is not None
    json_data = context.response.json()
    assert json_data is not None


@when('I look at the component analysis duration')
def look_at_component_analysis_duration(context):
    """Just dummy step to make test scenarios more readable."""
    assert context is not None
    assert context.duration is not None


@then('I should see that the component analysis duration is less than {duration:d} second')
@then('I should see that the component analysis duration is less than {duration:d} seconds')
def check_component_analysis_duration_in_seconds(context, duration):
    """Check the component analysis duration when the duration is specified in seconds."""
    # with very low probability, leap second might occur
    assert context.duration > 0, \
        "Duration is negative, it means that the leap second occured during component analysis"

    # check if the measured duration is less than maximum expected threshold
    assert context.duration < duration, \
        "Component analysis duration is too long: {} seconds instead of {}".format(
            duration, context.duration)


@then('I should see that the duration is less than {duration:d} minute')
@then('I should see that the duration is less than {duration:d} minutes')
def check_component_analysis_duration_in_minutes(context, duration):
    """Check the component analysis duration when the duration is specified in minutes."""
    # just use the existing code, with different units
    check_component_analysis_duration_in_seconds(context, duration * 60)


@then('I should find no recommendations in the component analysis')
def check_analyzed_no_reccomendation(context):
    """Check the number analyzed recommendations."""
    context_reponse_existence_check(context)
    json_data = context.response.json()

    assert "result" in json_data, "'result' node is expected to be found in the component analysis"
    result = json_data["result"]

    assert "recommendation" in result
    recommendation = result["recommendation"]
    assert recommendation == {}, "no recommendations are expected to be found in component analysis"


@then('I should find recommendation to change to version {version} in the component analysis')
def check_analyzed_reccomendation_version(context, version):
    """Check the the analyzed recommendations."""
    context_reponse_existence_check(context)
    json_data = context.response.json()

    assert "result" in json_data, "'result' node is expected to be found in the component analysis"
    result = json_data["result"]

    assert "recommendation" in result
    recommendation = result["recommendation"]

    assert "change_to" in recommendation
    change_to = recommendation["change_to"]
    assert change_to == version, "different version found {} != {}".format(version, change_to)


@then('I should find CVE report {cve} with score {score} in the component analysis')
def check_analyzed_cve(context, cve, score):
    """Check the the analyzed CVE."""
    context_reponse_existence_check(context)
    json_data = context.response.json()

    check_attribute_presence(json_data, "result")
    result = json_data["result"]

    check_attribute_presence(result, "recommendation")
    recommendation = result["recommendation"]

    check_attribute_presence(recommendation, "component-analyses")
    component_analyses = recommendation["component-analyses"]

    check_attribute_presence(component_analyses, "cve")
    cves = component_analyses["cve"]
    assert len(cves) >= 1

    for c in cves:
        check_attribute_presence(c, "id")
        check_attribute_presence(c, "cvss")
        check_cve_value(c["id"])
        if c["id"] == cve and str(c["cvss"]) == score:
            return

    raise Exception("Can not find CVE {} with score {}".format(cve, score))


@then('I should find one analyzed package in the component analysis')
@then('I should find {num:d} analyzed packages in the component analysis')
def check_analyzed_packages_count(context, num=1):
    """Check number of analyzed packages."""
    context_reponse_existence_check(context)
    json_data = context.response.json()

    check_attribute_presence(json_data, "result")
    result = json_data["result"]

    check_attribute_presence(result, "data")
    data = result["data"]
    assert len(data) == num, "{} packages expected, but found {} instead".format(num, len(data))


@then('I should find the package {package} from {ecosystem} ecosystem in the component analysis')
def check_analyzed_packages(context, package, ecosystem):
    """Check the package in component analysis."""
    context_reponse_existence_check(context)
    json_data = context.response.json()

    package_data = get_value_using_path(json_data, "result/data/0/package")
    assert package_data is not None

    check_attribute_presence(package_data, "ecosystem")
    assert package_data["ecosystem"][0] == ecosystem

    check_attribute_presence(package_data, "name")
    assert package_data["name"][0] == package


@then('I should find the component {package} version {version} from {ecosystem} ecosystem in '
      'the component analysis')
def check_analyzed_component(context, package, version, ecosystem):
    """Check the component in component analysis."""
    context_reponse_existence_check(context)
    json_data = context.response.json()

    version_data = get_value_using_path(json_data, "result/data/0/version")
    assert version_data is not None

    check_attribute_presence(version_data, "pecosystem")
    assert version_data["pecosystem"][0] == ecosystem

    check_attribute_presence(version_data, "pname")
    assert version_data["pname"][0] == package

    check_attribute_presence(version_data, "version")
    assert version_data["version"][0] == version


@then('I should find {num:d} components ({components}), all from {ecosystem} ecosystem')
@then('I should see 0 components')
@then('I should see {num:d} components ({components}), all from {ecosystem} ecosystem')
def check_components(context, num=0, components='', ecosystem=''):
    """Check that the specified number of components can be found."""
    components = split_comma_separated_list(components)

    json_data = context.response.json()

    search_results = json_data['result']
    assert len(search_results) == num
    for search_result in search_results:
        assert search_result['ecosystem'] == ecosystem
        assert search_result['name'] in components


def print_search_results(search_results):
    """Print all components that can be found."""
    print("\n\n\n")
    print("The following components can be found")
    for r in search_results:
        print(r)
    print("\n\n\n")


@then('I should find the analysis for the component {component} from ecosystem {ecosystem}')
def check_component_analysis_existence(context, component, ecosystem):
    """Check that the given component can be found in selected ecosystem."""
    json_data = context.response.json()
    search_results = json_data['result']

    for search_result in search_results:
        if ecosystem in search_result['ecosystem'] and \
           component in search_result['name']:
            return

    # print_search_results(search_results)

    raise Exception('Component {component} for ecosystem {ecosystem} could not be found'.
                    format(component=component, ecosystem=ecosystem))


@then('I should not find the analysis for the {component} from ecosystem {ecosystem}')
def check_component_analysis_nonexistence_in_ecosystem(context, component, ecosystem):
    """Check that the given component can not be found in the selected ecosystem."""
    json_data = context.response.json()
    search_results = json_data['result']

    for search_result in search_results:
        if search_result['ecosystem'] == ecosystem and \
           search_result['name'] == component:
            raise Exception('Component {component} for ecosystem {ecosystem} was found'.
                            format(component=component, ecosystem=ecosystem))


@then('I should not find the analysis for the {component} in any ecosystem')
def check_component_analysis_nonexistence_in_any_ecosystem(context, component):
    """Check that the given component can not be found in any ecosystem."""
    json_data = context.response.json()
    search_results = json_data['result']

    for search_result in search_results:
        if search_result['name'] == component:
            ecosystem = search_result['ecosystem']
            raise Exception('Component {component} for ecosystem {ecosystem} was found'.
                            format(component=component, ecosystem=ecosystem))
