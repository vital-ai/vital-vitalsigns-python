import argparse
import os
import sys
from vital_ai_vitalsigns.utils.find_vitalhome import find_vitalhome


class VitalSignsCommand:
    def __init__(self, args):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

        vital_home = find_vitalhome()

        if vital_home:
            self.vital_home = vital_home
        else:
            self.vital_home = ''

    def create_parser(self):

        parser = argparse.ArgumentParser(prog="vitalsigns", description="VitalSigns Command", add_help=True)
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        help_parser = subparsers.add_parser('help', help="Display help information")

        info_parser = subparsers.add_parser('info', help="Display information about the system and environment")

        # Generate command
        generate_parser = subparsers.add_parser('generate', help="Generate Ontology Binding")
        generate_parser.add_argument('-o', '--ontology', required=True, help="Ontology file path")

        # Cache command
        cache_parser = subparsers.add_parser('cache', help="Manage the registry cache")
        cache_subparsers = cache_parser.add_subparsers(dest="cache_action", help="Cache actions")
        cache_subparsers.add_parser('clear', help="Delete the registry cache file")
        cache_subparsers.add_parser('rebuild', help="Clear and rebuild the registry cache")
        cache_subparsers.add_parser('status', help="Show cache status")

        return parser

    def run(self):
        if self.args.command == 'help':
            self.parser.print_help()
        elif self.args.command == 'info':
            self.info()
        elif self.args.command == 'generate':
            self.generate()
        elif self.args.command == 'cache':
            self.cache()
        else:
            self.parser.print_help()

    def generate(self):

        input_path = os.path.join(self.vital_home, self.args.ontology) if not os.path.isabs(
            self.args.ontology) else self.args.ontology

        print(f"Generating files from {input_path}")

    def info(self):
        vital_home = self.vital_home
        print("VitalSigns Info")
        print(f"Current VITAL_HOME: {vital_home}")

    def cache(self):
        from vital_ai_vitalsigns.impl.vitalsigns_registry_cache import VitalSignsRegistryCache
        import json
        import time

        cache_path = VitalSignsRegistryCache.get_cache_path()
        action = self.args.cache_action

        if action == 'clear':
            if cache_path.exists():
                cache_path.unlink()
                print(f"Cache cleared: {cache_path}")
            else:
                print("No cache file found.")

        elif action == 'rebuild':
            if cache_path.exists():
                cache_path.unlink()
                print("Existing cache cleared.")

            print("Rebuilding cache (full scan)...")
            t0 = time.perf_counter()

            from vital_ai_vitalsigns.vitalsigns import VitalSigns
            vs = VitalSigns()

            elapsed = time.perf_counter() - t0
            registry = vs.get_registry()

            print(f"Cache rebuilt in {elapsed:.2f}s")
            print(f"  Classes: {len(registry.vitalsigns_classes)}")
            print(f"  Property classes: {len(registry.vitalsigns_property_classes)}")
            print(f"  Cache file: {cache_path}")
            if cache_path.exists():
                size = cache_path.stat().st_size
                print(f"  Cache size: {size:,} bytes ({size/1024:.1f} KB)")

        elif action == 'status':
            print(f"Cache path: {cache_path}")
            if cache_path.exists():
                size = cache_path.stat().st_size
                print(f"Cache exists: yes ({size:,} bytes, {size/1024:.1f} KB)")
                try:
                    with open(cache_path, 'r') as f:
                        cached = json.load(f)
                    print(f"Cache version: {cached.get('cache_version', 'unknown')}")
                    print(f"Cache key: {cached.get('cache_key', 'unknown')[:16]}...")
                    ts = cached.get('timestamp')
                    if ts:
                        from datetime import datetime
                        print(f"Created: {datetime.fromtimestamp(ts).isoformat()}")
                    print(f"Classes: {len(cached.get('vitalsigns_classes', {}))}")
                    print(f"Property classes: {len(cached.get('vitalsigns_property_classes', {}))}")

                    current_key = VitalSignsRegistryCache.compute_cache_key()
                    if current_key == cached.get('cache_key'):
                        print("Cache is VALID (key matches current packages)")
                    else:
                        print("Cache is STALE (packages have changed since cache was built)")
                except Exception as e:
                    print(f"Error reading cache: {e}")
            else:
                print("Cache exists: no")
        else:
            print("Usage: vitalsigns cache {clear|rebuild|status}")


def main():
    import sys
    command = VitalSignsCommand(sys.argv[1:])
    command.run()


if __name__ == "__main__":
    main()
