import {PerspectiveWidget} from "@finos/perspective-phosphor";
import {CommandRegistry} from "@phosphor/commands";
import {Menu, Widget} from "@phosphor/widgets";
import {DataLoader} from "phosphor-perspective-utils/data";
import {APIS} from "./define";

export interface ITab {
    tab: Widget; // Phosphor Widget
    loaders: DataLoader[]; // Data Loaders
    perspectives: PerspectiveWidget[]; // Perspective widgets
    menus: Menu[]; // menus
}

export
function fetcher(url: string): Promise<{[key: string]: string}> {
    return new Promise<{[key: string]: string}>((resolve) => {
        fetch(url, {method: "GET"})
            .then((response) => response.json())
            .then((json) => resolve(json.data));
        },
    );
}

export
function exchanges(): Promise<{[key: string]: string}> {
    return fetcher(APIS.EXCHANGES);
}

export
function instruments(): Promise<{[key: string]: string}> {
    return fetcher(APIS.INSTRUMENTS);
}

export
function exchanges_and_instruments(): Promise<{[key: string]: string[]}> {
    return new Promise<{[key: string]: string[]}>((resolve) => {
        exchanges().then((res) => {
            const exch = [] as string[];
            for (const val of res as any) {
                exch.push(val.name);
            }
            instruments().then((res2) => {
                const inst = [] as string[];
                for (const val of res2 as any) {
                    inst.push(val.underlying);
                }
                resolve({exchanges: exch, instruments: inst});
            });
        });
    });
}

export
function build_menu_commands(res: {[key: string]: string[]},
                             commands: CommandRegistry,
                             baseMenu: Menu,
                             baseCommand: string,
                             baseIcon= "fa fa-plus",
// tslint:disable-next-line: no-empty
                             execute= (exchange: string, instrument: string) => {},
    ): void {
    for (const exchange of res.exchanges) {

      const menu = new Menu({commands});
      menu.title.label = exchange;
      baseMenu.addItem({submenu: menu, type: "submenu"});

      for (const instrument of res.instruments) {
        const cmd = baseCommand + ":" + exchange + ":" + instrument;
        commands.addCommand(cmd, {
          execute: () => {
            execute(exchange, instrument);
          },
          iconClass: baseIcon,
          label: instrument,
          mnemonic: 2,
        });
        menu.addItem({command: cmd});
      }
    }
}
