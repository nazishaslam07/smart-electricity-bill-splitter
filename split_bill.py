import datetime
import os
from tabulate import tabulate
from fpdf import FPDF

def calculate_component_C(component_B, tax_rate):
    return component_B * (tax_rate / 100)

def calculate_cost(units, rate):
    return units * rate

def distribute_units(slabs, unit_consumptions):
    remaining_units = unit_consumptions.copy()
    costs = [0] * len(unit_consumptions)
    detailed_costs = [[] for _ in range(len(unit_consumptions))]
    
    for units, rate, ppac in slabs:
        unit_distribution = [min(units // len(unit_consumptions), remaining_units[i]) for i in range(len(unit_consumptions))]
        while sum(unit_distribution) < units and any(remaining_units):
            for i in range(len(unit_consumptions)):
                if sum(unit_distribution) < units and remaining_units[i] > unit_distribution[i]:
                    unit_distribution[i] += 1
        for i in range(len(unit_consumptions)):
            consumed_units = min(unit_distribution[i], remaining_units[i])
            cost = calculate_cost(consumed_units, rate)
            tax = calculate_component_C(cost, ppac)
            costs[i] += cost + tax
            detailed_costs[i].append((consumed_units, rate, ppac, cost, tax))
            remaining_units[i] -= consumed_units
    return costs, detailed_costs

def proportion(value, total):
    return value / total

def calculate_fixed_components_proportion(fixed_components_sum, unit_proportions):
    return [fixed_components_sum * proportion for proportion in unit_proportions]

def calculate_final_amounts(variable_costs, fixed_costs_proportion):
    return [variable_costs[i] + fixed_costs_proportion[i] for i in range(len(variable_costs))]

def save_to_file(data, filename):
    with open(filename, 'w') as file:
        file.write(data)

def generate_pdf_report(data, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Courier", size=8)  # Monospaced font for alignment

    for line in data.split("\n"):
        pdf.cell(0, 5, line, ln=True)
    pdf.output(filename)

def print_and_save_report(slabs, fixed_components, flat_names, unit_consumptions, variable_costs, detailed_costs, unit_proportions, fixed_components_sum, fixed_costs_proportion, final_amounts, rebate, rebate_shares, final_amounts_after_rebate, bill_month, bill_year):
    output = []

    # Flats and Their Units
    output.append("Flat and Units:")
    output.append(tabulate(
        [["Flat"] + flat_names, ["Units"] + unit_consumptions],
        headers="firstrow", tablefmt="grid"
    ))

    # Bill slabs and taxes
    output.append("\nBill slabs and taxes:")
    slabs_data = [["Units", "Rate", "PPAC (%)", "Cost (B)", "Tax", "Total (B+C)"]]
    for units, rate, ppac in slabs:
        cost = calculate_cost(units, rate)
        tax = calculate_component_C(cost, ppac)
        slabs_data.append([units, rate, ppac, cost, tax, cost + tax])
    output.append(tabulate(slabs_data, headers="firstrow", tablefmt="grid"))

    # Extra Components
    output.append("\nExtra Components:")
    components_data = [["Component"] + list(fixed_components.keys()), ["Amount"] + list(fixed_components.values())]
    output.append(tabulate(components_data, headers="firstrow", tablefmt="grid"))

    # Detailed Calculations for Each Flat
    for i, flat in enumerate(flat_names):
        output.append(f"\nDetailed Calculation for Flat {flat}:")
        detailed_data = [["Units", "Rate", "PPAC (%)", "Cost (B)", "Tax", "Total (B+C)"]]
        for units, rate, ppac, cost, tax in detailed_costs[i]:
            detailed_data.append([units, rate, ppac, cost, tax, cost + tax])
        output.append(tabulate(detailed_data, headers="firstrow", tablefmt="grid"))

    # Extras Table
    extras_data = [["Flat", "Units", "Proportions", "Extra Charges"]]
    for i, flat in enumerate(flat_names):
        extras_data.append([flat, unit_consumptions[i], unit_proportions[i], fixed_costs_proportion[i]])
    output.append("\nExtras Table:")
    output.append(tabulate(extras_data, headers="firstrow", tablefmt="grid"))

    # Final Amount Table
    final_amount_data = [
        ["", *flat_names],
        ["Units", *unit_consumptions],
        ["Slab Charges (B+C)", *[round(vc) for vc in variable_costs]],
        ["Extras", *[round(fp) for fp in fixed_costs_proportion]],
        ["Total Before Rebate", *[round(fa) for fa in final_amounts]],
        ["Rebate Share", *[f"-{round(rs)}" for rs in rebate_shares]],
        ["Net Payable", *[round(net) for net in final_amounts_after_rebate]]
    ]
    output.append("\nFinal Amount:")
    output.append(tabulate(final_amount_data, headers="firstrow", tablefmt="grid"))

    total_amount = sum(final_amounts)
    total_rebate = sum(rebate_shares)
    total_net = sum(final_amounts_after_rebate)
    output.append(f"\nTotal Amount Before Rebate: {total_amount:.2f}")
    output.append(f"Total Rebate Applied: {total_rebate:.2f}")
    output.append(f"Total Net Payable: {total_net:.2f}")

    output_str = "\n".join(output)
    print(output_str)
    
    # Convert to abbreviated month
    month_abbr = datetime.datetime.strptime(bill_month, '%B').strftime('%b')

    # Folder structure: data/Feb_2025/
    folder = f"data/{month_abbr}_{bill_year}/"
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Save files
    filename_txt = f"{folder}Bill_{month_abbr}_{bill_year}_Floor_{flat_names[0][0]}.txt"
    filename_pdf = f"{folder}Bill_{month_abbr}_{bill_year}_Floor_{flat_names[0][0]}.pdf"
    print('filename_txt',filename_txt)
    print('filename_pdf',filename_pdf)
    save_to_file(output_str, filename_txt)
    generate_pdf_report(output_str, filename_pdf)

if __name__ == "__main__":
    number_of_flats = input("Enter Number of Flats [3]: ")
    number_of_flats = int(number_of_flats) if number_of_flats else 3
    
    flat_names = []
    for i in range(number_of_flats):
        default_flat = str(401 + i)
        flat_name = input(f"Enter Name of Flat {i+1} [{default_flat}]: ")
        flat_names.append(flat_name if flat_name else default_flat)

    # Default to the previous month
    today = datetime.datetime.now()
    default_date = today.replace(day=1) - datetime.timedelta(days=1)
    bill_month = input(f"Enter Bill Month [{default_date.strftime('%B')}]: ") or default_date.strftime('%B')
    bill_year = input(f"Enter Bill Year [{default_date.year}]: ") or default_date.year

    default_slabs = [
        (198, 3, 35.83),
        (199, 4.5, 35.83),
        (396, 6.5, 35.83),
        (397, 7, 35.83),
        (160, 8, 35.83)
    ]

    slabs = []
    for i, (default_units, default_rate, default_ppac) in enumerate(default_slabs):
        units = input(f"Enter Component B slab {i+1} units [{default_units}]: ")
        units = int(units) if units else default_units
        rate = input(f"Enter Component B slab {i+1} rate [{default_rate}]: ")
        rate = float(rate) if rate else default_rate
        ppac = input(f"Enter PPAC % for slab {i+1} [{default_ppac}]: ")
        ppac = float(ppac) if ppac else default_ppac
        slabs.append((units, rate, ppac))

    default_fixed_components = {
        'A': 198.28,
        'D': 0,
        'E': 705.34,
        'F': 617.18,
        'G': 71.04,
        'H': 619.8,
        'I': 0,
        'J': 2.3
    }
    
    fixed_components = {}
    for component, default_value in default_fixed_components.items():
        value = input(f"Enter Component {component} [{default_value}]: ")
        fixed_components[component] = float(value) if value else default_value

    unit_consumptions = []
    for i, flat in enumerate(flat_names):
        default_units = 550 if i == 0 else 650 if i == 1 else 150  # Default for first 3 flats
        units = input(f"Enter {flat} units [{default_units}]: ")
        unit_consumptions.append(int(units) if units else default_units)

    variable_costs, detailed_costs = distribute_units(slabs, unit_consumptions)
    total_units = sum(unit_consumptions)
    unit_proportions = [proportion(units, total_units) for units in unit_consumptions]

    fixed_components_sum = sum(fixed_components.values())
    fixed_costs_proportion = calculate_fixed_components_proportion(fixed_components_sum, unit_proportions)

    final_amounts = calculate_final_amounts(variable_costs, fixed_costs_proportion)

    # Input rebate/subsidy
    rebate = input("Enter total Rebate/Subsidy amount [0]: ")
    rebate = float(rebate) if rebate else 0
    rebate_shares = [rebate * prop for prop in unit_proportions]
    final_amounts_after_rebate = [final_amounts[i] - rebate_shares[i] for i in range(len(final_amounts))]

    print_and_save_report(slabs, fixed_components, flat_names, unit_consumptions, variable_costs, detailed_costs, unit_proportions, fixed_components_sum, fixed_costs_proportion, final_amounts, rebate, rebate_shares, final_amounts_after_rebate, bill_month, bill_year)
