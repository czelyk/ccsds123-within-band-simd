ENTRY(_start)
SECTIONS {
 . = 0x80000000;
 .results (NOLOAD) : { *(.results) }
 . = 0x80001000;
 .text : { *(.text.start) *(.text*) }
 .rodata : { *(.rodata*) }
 .data : { *(.data*) *(.sdata*) }
 .bss (NOLOAD) : { *(.bss*) *(.sbss*) *(COMMON) }
 _image_end = .;
 _stack_top = 0x80fff000;
 ASSERT(_image_end < 0x80ff0000, "image and stack overlap")
 /DISCARD/ : { *(.comment) *(.eh_frame*) }
}
