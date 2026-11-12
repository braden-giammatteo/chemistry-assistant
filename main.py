import chempy
from chempy import Substance, balance_stoichiometry
from drafter import *
from dataclasses import dataclass
from bakery import assert_equal
from thermo import Chemical

set_site_information(
    author="Braden Giammatteo",
    description="A chemistry assistant that takes your experimental information, and then returns more complex information, like the theoretical yield or percent yield",
    sources=["thermo and chempy, and a variety of drafter documents"],
    planning=["https://docs.google.com/document/d/1XktjDm2B2RT84M2a9oGBxqw1T9zF5yJvkq4yXRyNIQE/edit?usp=sharing & https://docs.google.com/document/d/1byZX8o091RXfnSEK0pqWW-14x7S4T64dlgbS6aFnyt0/edit?usp=sharing"],
    links=["https://braden-giammatteo.github.io/chemistry-assistant/"]
'''Dataclasses'''

@dataclass
class compound:
    substance: Substance
    input_mass: float
    coefficient: int
    formula: str


'''t_yield is short for theoretical yield'''

@dataclass
class State:
    compounds: list[compound]
    heat_output: float
    t_yield: float
    product: compound


'''Helper Functions'''


def t_yield(state: State) -> float:
    '''Calculates theoretical yield based on initial reactant masses.'''

    product = state.product

    possible_yields = []

    for reactant in state.compounds:
        possible = (
            reactant.input_mass / reactant.substance.mass
            * (product.coefficient / reactant.coefficient)
            * product.substance.mass
        )

        possible_yields.append(possible)

    theoretical_yield = min(possible_yields)

    state.t_yield = theoretical_yield

    return theoretical_yield


def navigation_buttons(current_page: str) -> list:
    '''Creates navigation buttons for all pages except the current page.'''

    buttons = []

    if current_page != 'index':
        buttons.append(Button('Home', 'index'))

    if current_page != 'p_yield':
        buttons.append(Button('Percent Yield', 'p_yield'))

    if current_page != 'heat':
        buttons.append(Button('Heat Information', 'heat'))

    if current_page != 'theoretical_yield':
        buttons.append(Button('Theoretical Yield', 'theoretical_yield'))

    if current_page != 'l_reactant':
        buttons.append(Button('Limiting Reactant', 'l_reactant'))

    if current_page != 'remains':
        buttons.append(Button('Remaining Masses', 'remains'))

    return buttons


def make_water_state(
    hydrogen_mass: float,
    oxygen_mass: float,
    product_mass: float
) -> State:
    '''Creates a test state for the reaction of hydrogen and oxygen.'''

    hydrogen = Substance.from_formula('H2')
    oxygen = Substance.from_formula('O2')
    water = Substance.from_formula('H2O')

    return State(
        compounds=[
            compound(hydrogen, hydrogen_mass, 2, 'H2'),
            compound(oxygen, oxygen_mass, 1, 'O2')
        ],
        heat_output=None,
        t_yield=None,
        product=compound(water, product_mass, 2, 'H2O')
    )


'''Routes/pages'''


@route
def index(state: State) -> Page:
    '''Displays the home page, input fields, navigation, and balanced equation.'''

    content = [
        'Welcome to your chemistry assistant! Enter your chemical formulas and masses below.',
        TextBox('R1', 'Reactant 1 formula'),
        TextBox('R1_mass', 'Reactant 1 initial mass (g)'),
        TextBox('R2', 'Reactant 2 formula'),
        TextBox('R2_mass', 'Reactant 2 initial mass (g)'),
        TextBox('P1', 'Product formula'),
        TextBox('P1_mass', 'Product mass (g)'),
        Button('Save Inputs', 'save_inputs'),
    ]

    content.extend(navigation_buttons('index'))

    if state.compounds and state.product:

        R1 = state.compounds[0]
        R2 = state.compounds[1]
        Prod = state.product

        equation = (
            (str(R1.coefficient) + ' ' if R1.coefficient != 1 else '')
            + R1.substance.unicode_name
            + ' + '
            + (str(R2.coefficient) + ' ' if R2.coefficient != 1 else '')
            + R2.substance.unicode_name
            + ' → '
            + (str(Prod.coefficient) + ' ' if Prod.coefficient != 1 else '')
            + Prod.substance.unicode_name
        )

        content.append(
            'Your automatically balanced chemical equation is:'
        )
        content.append(equation)

    return Page(state, content)


@route
def save_inputs(state: State, R1: str, R1_mass: str,
                R2: str, R2_mass: str,
                P1: str, P1_mass: str) -> Page:
    '''Saves the entered formulas and masses and balances the equation.'''

    R1 = R1.strip()
    R2 = R2.strip()
    P1 = P1.strip()

    if (float(R1_mass) <= 0 or float(R2_mass) <= 0
            or float(P1_mass) <= 0):

        return Page(state, [
            'Masses must be greater than zero.',
            Button('Return Home', 'index')
        ])

    reactants, products = balance_stoichiometry(
        {R1, R2},
        {P1}
    )

    state.compounds = [
        compound(
            Substance.from_formula(R1),
            float(R1_mass),
            reactants[R1],
            R1
        ),

        compound(
            Substance.from_formula(R2),
            float(R2_mass),
            reactants[R2],
            R2
        )
    ]

    state.product = compound(
        Substance.from_formula(P1),
        float(P1_mass),
        products[P1],
        P1
    )

    return index(state)


@route
def p_yield(state: State) -> Page:
    '''Calculates and displays the percent yield of the reaction.'''

    if not state.compounds or state.product is None:
        return Page(state, [
            'You have not entered all the information yet.'
        ] + navigation_buttons('p_yield'))

    theoretical = t_yield(state)

    percent = state.product.input_mass / theoretical * 100

    if percent > 100:
        return Page(state, [
            'Your product likely contains impurities or there may be measurement errors, your percent yield exceeds 100%.',

            'Your calculated percent yield is: '
            + str(round(percent, 3)) + '%'
        ] + navigation_buttons('p_yield'))

    else:
        return Page(state, [
            'Your percent yield is: '
            + str(round(percent, 3)) + '%'
        ] + navigation_buttons('p_yield'))


@route
def theoretical_yield(state: State) -> Page:
    '''Calculates and displays the theoretical yield of the reaction.'''

    if not state.compounds or state.product is None:
        return Page(state, [
            'Please enter your reaction information first.'
        ] + navigation_buttons('theoretical_yield'))

    Prod = state.product

    return Page(state, [
        'The theoretical yield for your balanced equation is: '
        + str(round(t_yield(state), 3))
        + ' g '
        + Prod.substance.unicode_name
    ] + navigation_buttons('theoretical_yield'))


@route
def l_reactant(state: State) -> Page:
    '''Identifies and displays the limiting reactant.'''

    if not state.compounds or state.product is None:
        return Page(state, [
            'Please enter your reaction information first.'
        ] + navigation_buttons('l_reactant'))

    ratios = [
        reactant.input_mass / reactant.substance.mass / reactant.coefficient
        for reactant in state.compounds
    ]

    smallest = min(ratios)

    limiting = [
        reactant.substance.unicode_name
        for reactant, ratio in zip(state.compounds, ratios)
        if ratio == smallest
    ]

    return Page(state, [
        'Your limiting reactant is: ' + ', '.join(limiting)
    ] + navigation_buttons('l_reactant'))


@route
def heat(state: State) -> Page:
    '''Calculates the heat of reaction and classifies the reaction.'''

    if not state.compounds or state.product is None:
        return Page(state, [
            'Please enter your reaction information first.'
        ] + navigation_buttons('heat'))

    product_chemical = Chemical(state.product.formula)
    product_heat = product_chemical.Hfm

    if product_heat is None:
        return Page(state, [
            'Heat of formation data is unavailable for '
            + state.product.formula
        ] + navigation_buttons('heat'))

    total_product_heat = (
        product_heat * state.product.coefficient
    )

    reactant_heat = 0

    for reactant in state.compounds:

        chemical = Chemical(reactant.formula)

        if chemical.Hfm is None:
            return Page(state, [
                'Heat of formation data is unavailable for '
                + reactant.formula
            ] + navigation_buttons('heat'))

        reactant_heat += chemical.Hfm * reactant.coefficient

    heat_change = total_product_heat - reactant_heat

    kJ_per_mole = (
        heat_change / state.product.coefficient / 1000
    )

    state.heat_output = kJ_per_mole

    if kJ_per_mole > 0:
        thermic = 'endothermic'

    elif kJ_per_mole < 0:
        thermic = 'exothermic'

    else:
        thermic = 'neither endothermic nor exothermic'

    actual_heat = (
        kJ_per_mole
        * state.product.input_mass
        / state.product.substance.mass
    )

    return Page(state, [
        'Your heat of reaction is: '
        + str(round(kJ_per_mole, 3))
        + ' kJ per mole of product.',

        'Your reaction is ' + thermic + '.',

        'Heat flow for your actual product amount: '
        + str(round(actual_heat, 3))
        + ' kJ.'
    ] + navigation_buttons('heat'))


@route
def remains(state: State) -> Page:
    '''Calculates and displays the remaining mass of each reactant.'''

    if not state.compounds:
        return Page(state, [
            'Please enter your reactants first.'
        ] + navigation_buttons('remains'))

    reaction_extent = min(
        reactant.input_mass
        / reactant.substance.mass
        / reactant.coefficient
        for reactant in state.compounds
    )

    results = ['Remaining reactant masses:']

    for reactant in state.compounds:

        consumed_mass = (
            reaction_extent
            * reactant.coefficient
            * reactant.substance.mass
        )

        remaining = max(0, reactant.input_mass - consumed_mass)

        results.append(
            reactant.substance.unicode_name
            + ': '
            + f'{remaining:.3f} g remaining'
        )

    return Page(
        state,
        results + navigation_buttons('remains')
    )


'''Unit Tests'''



def page_text(result: Page) -> str:
    """Combines page content into text for route tests."""
    return ' '.join(str(item) for item in result.content)


def test_index_route() -> None:
    """Tests the home message and presence of the save button."""
    state = State(None, None, None, None)

    result = index(state)
    content = page_text(result)

    assert 'Enter your chemical formulas and masses below.' in content
    assert 'Save Inputs' in content


def test_save_inputs_route() -> None:
    """Tests that valid inputs are saved with balanced coefficients."""
    state = State(None, None, None, None)

    save_inputs(state, 'H2', '4', 'O2', '32', 'H2O', '18')

    assert_equal(len(state.compounds), 2)
    assert_equal(state.product.formula, 'H2O')
    assert_equal(state.compounds[0].coefficient, 2)
    assert_equal(state.compounds[1].coefficient, 1)
    assert_equal(state.product.coefficient, 2)


def test_p_yield_route() -> None:
    """Tests the calculated percent yield shown on the page."""
    hydrogen = Substance.from_formula('H2')
    oxygen = Substance.from_formula('O2')
    water = Substance.from_formula('H2O')

    state = make_water_state(
        2 * hydrogen.mass,
        oxygen.mass,
        water.mass
    )

    result = p_yield(state)
    content = page_text(result)

    assert_equal(state.t_yield, 2 * water.mass)
    assert '50.0%' in content


def test_theoretical_yield_route() -> None:
    """Tests the theoretical yield value and product shown on the page."""
    hydrogen = Substance.from_formula('H2')
    oxygen = Substance.from_formula('O2')
    water = Substance.from_formula('H2O')

    state = make_water_state(
        2 * hydrogen.mass,
        oxygen.mass,
        water.mass
    )

    result = theoretical_yield(state)
    content = page_text(result)
    expected_yield = 2 * water.mass

    assert_equal(state.t_yield, expected_yield)
    assert str(round(expected_yield, 3)) in content
    assert water.unicode_name in content


def test_l_reactant_route() -> None:
    """Tests that the page identifies oxygen as the limiting reactant."""
    hydrogen = Substance.from_formula('H2')
    oxygen = Substance.from_formula('O2')
    water = Substance.from_formula('H2O')

    state = make_water_state(
        2 * hydrogen.mass,
        0.5 * oxygen.mass,
        water.mass
    )

    result = l_reactant(state)
    content = page_text(result)

    assert oxygen.unicode_name in content
    assert hydrogen.unicode_name not in content


def test_heat_route() -> None:
    """Tests that valid water reaction data produces an exothermic result."""
    hydrogen = Substance.from_formula('H2')
    oxygen = Substance.from_formula('O2')
    water = Substance.from_formula('H2O')

    state = make_water_state(
        2 * hydrogen.mass,
        oxygen.mass,
        water.mass
    )

    result = heat(state)
    content = page_text(result)

    assert state.heat_output is not None
    assert state.heat_output < 0
    assert 'exothermic' in content
    assert 'kJ per mole of product' in content


def test_remains_route() -> None:
    """Tests the remaining reactant masses displayed by the page."""
    hydrogen = Substance.from_formula('H2')
    oxygen = Substance.from_formula('O2')
    water = Substance.from_formula('H2O')

    state = make_water_state(
        2 * hydrogen.mass,
        2 * oxygen.mass,
        water.mass
    )

    result = remains(state)
    content = page_text(result)

    expected_oxygen_remaining = round(oxygen.mass, 3)

    assert hydrogen.unicode_name in content
    assert oxygen.unicode_name in content
    assert '0.000 g remaining' in content
    assert str(expected_oxygen_remaining) in content
    assert 'g remaining' in content

test_index_route()
test_save_inputs_route()
test_p_yield_route()
test_theoretical_yield_route()
test_l_reactant_route()
test_heat_route()
test_remains_route()

    
    
start_server(State(
    compounds=None,
    heat_output=None,
    t_yield=None,
    product=None
))
