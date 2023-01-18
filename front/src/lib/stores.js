import { writable } from 'svelte/store';

let indicateursExternesField = document.getElementById("id_indicateurs_externes_in_step")

export const indicateursExternes = writable(JSON.parse(indicateursExternesField.value));