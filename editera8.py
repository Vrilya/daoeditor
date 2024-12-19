from gff4 import read_header, read_gff4
import json

# Dictionary to map field IDs to their names
FIELD_NAMES = {
    16300: "Base",
    16301: "Modifier",
    16302: "Current",
    16303: "Combat regen",
    16304: "Regen"
}

def load_stat_names():
    """Load the stat names from stats.json file."""
    with open('stats.json', 'r') as f:
        stats = json.load(f)
    # Create a reverse mapping from ID to name
    return {v: k for k, v in stats.items()}

def get_field_name(field_label):
    """Convert field label to human-readable name if available."""
    return FIELD_NAMES.get(field_label, str(field_label))

def inspect_attributes(struct_cps1, stat_names):
    """Inspect attributes in StructCPS1."""
    if hasattr(struct_cps1, "_dict") and 16350 in struct_cps1._dict:
        attributes = struct_cps1._dict[16350]  # ListGeneric object
        if hasattr(attributes, "_list"):
            print("\nAttributes (from 16350):")
            for i, attr in enumerate(attributes._list):
                if hasattr(attr, "fields"):
                    # Get the attribute type ID using the correct field access method
                    attr_type = int(attr[16353])  # Convert to int to match our JSON keys
                    attr_name = stat_names.get(attr_type, f"Unknown({attr_type})")
                    print(f"  Attribute {attr_type} {attr_name}:")
                    for field in attr.fields:
                        if field.label != 16353:  # Skip printing the type ID since we now show it in the header
                            field_name = get_field_name(field.label)
                            print(f"    {field_name}: {attr[field.label]}")
                else:
                    print(f"  Attribute {i} is not a structured object.")
        else:
            print("16350 does not contain a valid list.")
    else:
        print("StructCPS1 does not contain key 16350.")

def explore_main_character(data, stat_names):
    """Explore the main character's information."""
    try:
        player = data[16002]  # Main character structure
        crp1 = player[16208]  # Main character's data
        cps1 = crp1[16209]  # Stats for the main character

        # Get character's name
        character_name_obj = crp1[16255] if 16255 in crp1 else "Unknown Name"
        if isinstance(character_name_obj, object) and hasattr(character_name_obj, 's'):
            character_name = character_name_obj.s.strip('\x00')
        else:
            character_name = "Unknown Name"
        print(f"Main Character's Name: {character_name}")

        # Inspect ATTR structures in 16350
        attr_list = cps1[16350]
        print("\nMain Character Attribute Structures:")
        for i, attr in enumerate(attr_list._list):
            if isinstance(attr, object) and hasattr(attr, 'fields'):
                # Get the attribute type ID using the correct field access method
                attr_type = int(attr[16353])  # Convert to int to match our JSON keys
                attr_name = stat_names.get(attr_type, f"Unknown({attr_type})")
                print(f"\nAttribute {attr_type} {attr_name}:")
                for field in attr.fields:
                    if field.label != 16353:  # Skip printing the type ID
                        field_name = get_field_name(field.label)
                        value = attr[field.label]
                        print(f"    {field_name}: {value}")
    except Exception as e:
        print(f"Error exploring main character: {e}")
        raise  # Re-raise the exception to see the full traceback

def explore_party_members(data, stat_names):
    """Explore party member data and extract attributes."""
    try:
        party_struct = data._dict.get(16003)  # StructPRTY
        if not party_struct:
            print("No party structure found under key 16003.")
            return

        party_list = party_struct._dict.get(16204)  # ListStructCRL1
        if not party_list or not hasattr(party_list, "_list"):
            print("No party members found in ListStructCRL1.")
            return

        print("\nExploring Party Members:")
        for i, member in enumerate(party_list._list):
            print(f"\nParty Member {i}:")
            if hasattr(member, "_dict"):
                # Fetch name from Key 3
                name_key = member._dict.get(3)  # ECString with character name
                if name_key:
                    name = getattr(name_key, 's', None) or str(name_key)
                else:
                    name = "Unknown (name_key missing)"
                print(f"  Name: {name}")

                # Inspect attributes in StructCPS1
                struct_cps1 = member._dict.get(16209)  # StructCPS1
                if struct_cps1:
                    print("  Inspecting Attributes:")
                    inspect_attributes(struct_cps1, stat_names)
                else:
                    print("  StructCPS1 not found.")
            else:
                print("  Party member has no valid _dict attribute.")
    except Exception as e:
        print(f"Error while exploring party members: {e}")
        raise  # Re-raise the exception to see the full traceback

def main():
    try:
        # Load the stat names first
        stat_names = load_stat_names()
        
        with open("savegame2.das", 'rb') as f:
            header = read_header(f)
            data = read_gff4(f, header)

            print("\nExploring Main Character:")
            explore_main_character(data, stat_names)

            print("\nExploring Party Members:")
            explore_party_members(data, stat_names)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()