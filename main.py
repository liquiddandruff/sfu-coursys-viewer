from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup as bs
import twill.commands as tw
import ConfigParser, os, pprint

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(CURR_DIR, "templates")
CONFIG_FILE = "config.ini"

AUTH_URL = "https://cas.sfu.ca/cas/login"
SYS_REDIRECT_URL = "https://cas.sfu.ca/cas/login?service=https%3A%2F%2Fcourses.cs.sfu.ca%2Flogin%2F%3Fnext%3D%252F"

pp = pprint.PrettyPrinter(indent=4)

def loadConfigIfExists():
    cp = ConfigParser.RawConfigParser()
    if len(cp.read(CONFIG_FILE)) == 0 or cp.sections().count('Account') == 0:
        return "", ""
    # yes... for dev only
    username = cp.get('Account', 'user')
    password = cp.get('Account', 'pass')
    return username, password


def authAndRedirect(username, password):
    tw.reset_browser()
    tw.go(SYS_REDIRECT_URL)
    tw.fv('1', "username", username)
    tw.fv('1', "password", password)
    tw.formaction('1', AUTH_URL)
    tw.submit()
    return tw.get_browser().get_html()

def extractDataFromCoursesListPage(courses_list):
    data = []
    for index, link in enumerate(courses_list.select(".sf-menu .header ul a")):
        curr = {'href': link['href'],
                'val': link.text}
        data.append(curr)
        print str(index) + "\t" + link['href'] + "\t" + link.string
    return data

def extractRowDataFromTable(table):
    data = [row for row in table.select("tbody tr")]
    return data

def extractDataFromCurrentCoursePage(current_course_page):
    data = {}
    course_tables = current_course_page.select(".parsys.main_content table")
    info_rows = extractRowDataFromTable(course_tables[0])
    activity_rows = extractRowDataFromTable(course_tables[1])

    data['info'] = {}
    for row in info_rows:
        heading = row.find('th').text.strip().lower().replace(' ', '_').replace('(s)', '')
        value = row.find('td').text.strip()
        data['info'][heading] = value

    data['activities'] = []
    for row in activity_rows:
        curr_activity = {}
        # activity name column
        current_cell = row.find_next('a')
        curr_activity['name'] = current_cell.text.strip()
        curr_activity['href'] = current_cell['href']
        # due date column
        current_cell = current_cell.find_next('td')
        curr_activity['due_date'] = current_cell.text.strip()
        # status column
        current_cell = current_cell.find_next('td')
        curr_activity['status'] = current_cell.text.strip()
        # grade column
        current_cell = current_cell.find_next('td')
        curr_activity['grade'] = current_cell.text.strip()

        data['activities'].append(curr_activity)

    return data

def renderToDisk(data):
    jj_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True)
    test_html = jj_env.get_template('entry.html')
    test_html = test_html.render(activities = data['activities'],
                     info = data['info'])
    with open("index.html", 'w') as test_html_file:
        test_html_file.write(test_html)


if __name__ == "__main__":
    username, password = loadConfigIfExists()
    redirection_html = bs(authAndRedirect(username, password))
    courses_list_data = extractDataFromCoursesListPage(redirection_html)

    tw.go(courses_list_data[2]['href'])

    current_course_page = bs(tw.get_browser().get_html())
    current_course_data = extractDataFromCurrentCoursePage(current_course_page)

    renderToDisk(current_course_data)


