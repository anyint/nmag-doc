(* $Id$ *)

(* Simple example showing how to use gtk2 widgets and stuff
   from within OCaml.
*)

#use "topfind";;
#require "lablgtk2";;
#require "lablgtk2.init";;
#require "lablgtk2.gtkgl";;

open GMain

let xpm_label_box ~(window : #GContainer.container)
    ~file ~text ?packing ?(show=true) () =
  if not (Sys.file_exists file) then failwith (file ^ " does not exist");
  let box = GPack.hbox ~border_width: 2 ?packing ~show:false () in
  let pixmap = GDraw.pixmap_from_xpm ~file ~window () in
  GMisc.pixmap pixmap ~packing:(box#pack ~padding:3) ();
  GMisc.label ~text ~packing:(box#pack ~padding:3) ();
  if show then box#misc#show ();
  new GObj.widget_full box#as_widget

let main () =
  let window = GWindow.window ~title:"Pixmap'd Buttons!" ~border_width:10 () in
  window#connect#destroy ~callback:Main.quit;
  let hbox = GPack.hbox ~packing:window#add () in
  let button = GButton.button ~packing:(hbox#pack ~padding:5) () in
  button#connect#clicked ~callback:
    (fun () -> prerr_endline "Hello again - cool button was pressed");
  xpm_label_box ~window ~file:"test.xpm" ~text:"cool button"
    ~packing:button#add ();
  let button = GButton.button ~use_mnemonic:true ~label:"_Coucou" ~packing:(hbox#pack ~padding:5) () in
  button#connect#clicked ~callback:
    (fun () -> prerr_endline "Coucou");
  let button = GButton.button ~stock:`HOME ~packing:(hbox#pack ~padding:5) () in
  button#connect#clicked ~callback:
    (fun () -> prerr_endline "Stock buttons look nice");
  window#show ();
  Main.main ()

let _ = main ()
