class WaterWorks: # survetorustikud
    def __init__(self):
        self.pumpla_1 = "10" # kui vooluhulk on kuni 10 m³/d, peab kuja olema 10 meetrit
        self.pumpla_2 = "20" # kui vooluhulk on üle 10 m³/d, peab kuja olema 20 meetrit
        self.purgimissõlm = "30"  # Purgimissõlme kuja peab olema 30 meetrit
        self.survetorustik_1 = "2" # alla 250 mm siseläbimõõduga torustikul 2 m
        self.survetorustik_2 = "2.5" # 250 mm kuni alla 500 mm siseläbimõõduga torustikul 2,5 m
        self.survetorustik_3 = "3" # 500 mm ja suurema siseläbimõõduga torustikul 3 m
        self.vabavoolsed_torustikud_1 = "2" # siseläbimõõt on alla 250 mm ja mis on paigaldatud kuni 2 m sügavusele, – 2 m
        self.vabavoolsed_torustikud_2 = "2.5" # siseläbimõõt on alla 250 mm ja mis on paigaldatud sügavamale kui 2 m, – 2,5 m
        self.vabavoolsed_torustikud_3 = "2.5" # siseläbimõõt on 250 mm ja suurem ning mis on paigaldatud kuni 2 m sügavusele, – 2,5 m
        self.vabavoolsed_torustikud_4 = "3" # siseläbimõõt on 250 kuni siseläbimõõduni, mis jääb alla 1000 mm, ning mis on paigaldatud sügavamale kui 2 m, – 3 m
        self.vabavoolsed_torustikud_5 = "5" # siseläbimõõt on 1000 mm ja suurem ning mis on paigaldatud sügavamale kui 2 m või allmaakaeveõõnesse, – 5 m


        self.tee_servituut = "3.5" # 3,5 m tee keskteljest

    @staticmethod
    def get_rule_info(inner_diameter = None, depth = None, Flow = None):
        # Define the conditions for each rule based on inner diameter and depth
        rule_1 = inner_diameter <= '250' and depth <= '2'
        rule_2 = inner_diameter <= '250' and depth > '2'
        rule_3 = inner_diameter > '250' and depth <= '2'
        rule_4 = '250' < inner_diameter < '1000' and depth > '2'
        rule_5 = inner_diameter >= '1000'
        rule_6 = depth <= '10'  # kui vooluhulk on kuni 10 m³/d, peab kuja olema 10 meetrit
        rule_7 = depth > '10'  # kui vooluhulk on üle 10 m³/d, peab kuja olema 20 meetrit
        rule_8 = depth == '30'  # Purgimissõlme kuja peab olema 30 meetrit
        water_rule_1 = inner_diameter <= '250' and depth <= '2'
        water_rule_2 = '250' < inner_diameter <= '500' and depth <= '2,5'
        water_rule_3 = inner_diameter > '500' and depth <= '3'

        restrictions = {
            WaterWorks().vabavoolsed_torustikud_1: rule_1, 
            WaterWorks().vabavoolsed_torustikud_2: rule_2,
            WaterWorks().vabavoolsed_torustikud_3: rule_3,    
            WaterWorks().vabavoolsed_torustikud_4: rule_4,
            WaterWorks().vabavoolsed_torustikud_5: rule_5,
            WaterWorks().pumpla_1: rule_6,
            WaterWorks().pumpla_2: rule_7,        
            WaterWorks().purgimissõlm: rule_8,
            WaterWorks().survetorustik_1: water_rule_1,
            WaterWorks().survetorustik_2: water_rule_2,
            WaterWorks().survetorustik_3: water_rule_3
                }

        return restrictions
    

class WaterWorksLinks:
    link_1 = "https://www.riigiteataja.ee/akt/114092023002" # "Ühisveevärgi ja -kanalisatsiooni kaitsevööndi ulatus"
    link_2 = "https://www.riigiteataja.ee/akt/106082019008" # "Kanalisatsiooniehitise planeerimise, ehitamise ja kasutamise nõuded ning..."
    link_3 = "https://www.riigiteataja.ee/akt/170179" # "Teeseadus" § 13.Tee kaitsevöönd

class Electrisity: 
    elekter_1 = "2" # kuni 1 kV pingega liinide korral 2 meetrit
    elekter_2 = "3" # 1 kuni 20 kV pingega liinidel õhukaabli kasutamise korral 3 meetrit
    elekter_3 = "10" # 1 kuni 20 kV pingega liinide korral 10 meetrit
    elekter_4 = "25" # 35–110 kV pingega liinide korral 25 meetrit
    elekter_5 = "40" # 220–330 kV pingega liinide korral 40 meetrit

class ElectricityLinks:
    link_1 ="https://www.riigiteataja.ee/akt/103022022020" # "Ehitise kaitsevööndi ulatus, kaitsevööndis tegutsemise kord ja..." § 10.Elektripaigaldise kaitsevööndi ulatus

class KaugKüte:
    maa_alused_soojustorustikud_1 = "2" # alla 200 mm läbimõõduga torustiku korral 2 meetrit
    maa_alused_soojustorustikud_2 = "3" # 200 mm ja suurema läbimõõduga torustiku korral 3 meetrit
    maapealsed_soojustorustikud = "10" # aurutorustikul töörõhul üle 16 baari on 10 meetrit
    maapealsed_soojustorustikud = "5" # aurutorustikul töörõhul 16 baari ja alla selle on 5 meetrit
    maapealsed_soojustorustikud = "5" # veetorustikul töörõhul üle 6 baari on 5 meetrit
    maapealsed_soojustorustikud = "2" # veetorustikul töörõhul 6 baari ja alla selle on 2 meetrit
    vedelkütusetorustik = "5" # torustiku välisseina äärmistest punktidest 5 meetrit

class KaugküteLinks:
    link_1 ="https://www.riigiteataja.ee/akt/103022022020" # "Ehitise kaitsevööndi ulatus, kaitsevööndis tegutsemise kord ja..." § 11.Kaugküttevõrgu ehitiste kaitsevöönd ja § 12.Vedelkütusetorustike kaitsevöönd

class GaasiTorustik:
    gaasitorustik_1 = "1" # A- ja B-kategooria gaasipaigaldiste korral torustiku välimisest mõõtmest 1 meetrit
    gaasitorustik_2 = "2" # C-kategooria gaasipaigaldise korral torustiku välimisest mõõtmest 2 meetrit
    gaasitorustik_3 = "3" # D-kategooria gaasipaigaldise nimiläbimõõduga <200 mm torustiku korral torustiku keskjoonest 3 meetrit
    gaasitorustik_4 = "5" # D-kategooria gaasipaigaldise nimiläbimõõduga ≥200 mm ja <500 mm torustiku korral torustiku keskjoonest 5 meetrit
    gaasitorustik_5 = "10" # D-kategooria gaasipaigaldise nimiläbimõõduga ≥500 mm torustiku korral torustiku keskjoonest 10 meetrit

class GaasitorustikLinks:
    link_1 ="https://www.riigiteataja.ee/akt/103022022020" # "Ehitise kaitsevööndi ulatus, kaitsevööndis tegutsemise kord ja..." § 13.Gaasitorustike kaitsevööndid

class sideehitis:
    sideehitis_maismaal = "1" # maismaal – 1 meeter sideehitisest või sideehitise välisseinast sideehitisega paralleelse mõttelise jooneni või tõmmitsatega raadiomasti korral 1 meeter välimiste tõmmitsate vundamendi välisservast ühendades tõmmitsad mõtteliseks kolmnurgaks, vabalt seisva masti korral 1 meeter vundamendi välisservast
    sideehitis_siseveekogudel = "100" # 100 meetrit sideehitise keskjoonest
    sideehitis_merel = "0,25" # 0,25 meremiili sideehitise keskjoonest

class SideehitiskLinks:
    link_1 ="https://www.riigiteataja.ee/akt/103022022020" # "Ehitise kaitsevööndi ulatus, kaitsevööndis tegutsemise kord ja..." § 14.Sideehitise kaitsevöönd


class GetRuledRestriction:

    @staticmethod
    def check_waterworks_rule(inner_diameter=None, depth=None, Flow=None):
        # Get the rule information based on the provided inner diameter and depth
        restrictions = WaterWorks.get_rule_info(inner_diameter, depth, Flow)

        # Find the applicable restriction
        applicable_restriction = None
        for rule, condition in restrictions.items():
            if condition:
                applicable_restriction = rule
                break

        return applicable_restriction