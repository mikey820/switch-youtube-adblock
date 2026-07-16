.text
.org 0x190e9a0

.global youtube_adblock_hook
youtube_adblock_hook:
    sub sp, sp, #0x60
    str x30, [sp, #0x58]

    // BrowserModule::web_module_.
    ldr x0, [x19, #0x590]
    cbz x0, 1f

    // Fake a read-only long std::string for the injected 475-byte script.
    mov x8, #0x1e1
    str x8, [sp, #0x00]
    mov x8, #475
    str x8, [sp, #0x08]
    .inst 0x90009768
    add x8, x8, #0xd24
    str x8, [sp, #0x10]

    // base::SourceLocation("[adblock]", 1, 1).
    mov x8, #0x11
    str x8, [sp, #0x18]
    mov x8, #9
    str x8, [sp, #0x20]
    .inst 0x90009768
    add x8, x8, #0xf00
    str x8, [sp, #0x28]
    mov w8, #1
    str w8, [sp, #0x30]
    str w8, [sp, #0x34]

    // WebModule::ExecuteJavascript(script, location, nullptr).
    add x8, sp, #0x38
    add x1, sp, #0x00
    add x2, sp, #0x18
    mov x3, xzr
    .inst 0x97a3e0a7

    // Destroy the returned std::string if it used heap storage.
    ldrb w8, [sp, #0x38]
    tbz w8, #0, 1f
    ldr x0, [sp, #0x48]
    .inst 0x97fff7cb

1:
    // Recreate the BrowserModule::OnLoad instruction replaced by the hook branch.
    add x0, x19, #0x598
    ldr x30, [sp, #0x58]
    add sp, sp, #0x60
    ret
