
Memloader:     file format elf64-x86-64


Disassembly of section .init:

00000000004004b0 <_init>:
  4004b0:	48 83 ec 08          	sub    $0x8,%rsp
  4004b4:	e8 b3 00 00 00       	callq  40056c <call_gmon_start>
  4004b9:	e8 42 01 00 00       	callq  400600 <frame_dummy>
  4004be:	e8 dd 05 00 00       	callq  400aa0 <__do_global_ctors_aux>
  4004c3:	48 83 c4 08          	add    $0x8,%rsp
  4004c7:	c3                   	retq   

Disassembly of section .plt:

00000000004004c8 <printf@plt-0x10>:
  4004c8:	ff 35 0a 0d 20 00    	pushq  0x200d0a(%rip)        # 6011d8 <_GLOBAL_OFFSET_TABLE_+0x8>
  4004ce:	ff 25 0c 0d 20 00    	jmpq   *0x200d0c(%rip)        # 6011e0 <_GLOBAL_OFFSET_TABLE_+0x10>
  4004d4:	0f 1f 40 00          	nopl   0x0(%rax)

00000000004004d8 <printf@plt>:
  4004d8:	ff 25 0a 0d 20 00    	jmpq   *0x200d0a(%rip)        # 6011e8 <_GLOBAL_OFFSET_TABLE_+0x18>
  4004de:	68 00 00 00 00       	pushq  $0x0
  4004e3:	e9 e0 ff ff ff       	jmpq   4004c8 <_init+0x18>

00000000004004e8 <memset@plt>:
  4004e8:	ff 25 02 0d 20 00    	jmpq   *0x200d02(%rip)        # 6011f0 <_GLOBAL_OFFSET_TABLE_+0x20>
  4004ee:	68 01 00 00 00       	pushq  $0x1
  4004f3:	e9 d0 ff ff ff       	jmpq   4004c8 <_init+0x18>

00000000004004f8 <malloc@plt>:
  4004f8:	ff 25 fa 0c 20 00    	jmpq   *0x200cfa(%rip)        # 6011f8 <_GLOBAL_OFFSET_TABLE_+0x28>
  4004fe:	68 02 00 00 00       	pushq  $0x2
  400503:	e9 c0 ff ff ff       	jmpq   4004c8 <_init+0x18>

0000000000400508 <__libc_start_main@plt>:
  400508:	ff 25 f2 0c 20 00    	jmpq   *0x200cf2(%rip)        # 601200 <_GLOBAL_OFFSET_TABLE_+0x30>
  40050e:	68 03 00 00 00       	pushq  $0x3
  400513:	e9 b0 ff ff ff       	jmpq   4004c8 <_init+0x18>

0000000000400518 <strtol@plt>:
  400518:	ff 25 ea 0c 20 00    	jmpq   *0x200cea(%rip)        # 601208 <_GLOBAL_OFFSET_TABLE_+0x38>
  40051e:	68 04 00 00 00       	pushq  $0x4
  400523:	e9 a0 ff ff ff       	jmpq   4004c8 <_init+0x18>

0000000000400528 <signal@plt>:
  400528:	ff 25 e2 0c 20 00    	jmpq   *0x200ce2(%rip)        # 601210 <_GLOBAL_OFFSET_TABLE_+0x40>
  40052e:	68 05 00 00 00       	pushq  $0x5
  400533:	e9 90 ff ff ff       	jmpq   4004c8 <_init+0x18>

Disassembly of section .text:

0000000000400540 <_start>:
  400540:	31 ed                	xor    %ebp,%ebp
  400542:	49 89 d1             	mov    %rdx,%r9
  400545:	5e                   	pop    %rsi
  400546:	48 89 e2             	mov    %rsp,%rdx
  400549:	48 83 e4 f0          	and    $0xfffffffffffffff0,%rsp
  40054d:	50                   	push   %rax
  40054e:	54                   	push   %rsp
  40054f:	49 c7 c0 00 0a 40 00 	mov    $0x400a00,%r8
  400556:	48 c7 c1 10 0a 40 00 	mov    $0x400a10,%rcx
  40055d:	48 c7 c7 60 07 40 00 	mov    $0x400760,%rdi
  400564:	e8 9f ff ff ff       	callq  400508 <__libc_start_main@plt>
  400569:	f4                   	hlt    
  40056a:	90                   	nop
  40056b:	90                   	nop

000000000040056c <call_gmon_start>:
  40056c:	48 83 ec 08          	sub    $0x8,%rsp
  400570:	48 8b 05 51 0c 20 00 	mov    0x200c51(%rip),%rax        # 6011c8 <_DYNAMIC+0x1a0>
  400577:	48 85 c0             	test   %rax,%rax
  40057a:	74 02                	je     40057e <call_gmon_start+0x12>
  40057c:	ff d0                	callq  *%rax
  40057e:	48 83 c4 08          	add    $0x8,%rsp
  400582:	c3                   	retq   
  400583:	90                   	nop
  400584:	90                   	nop
  400585:	90                   	nop
  400586:	90                   	nop
  400587:	90                   	nop
  400588:	90                   	nop
  400589:	90                   	nop
  40058a:	90                   	nop
  40058b:	90                   	nop
  40058c:	90                   	nop
  40058d:	90                   	nop
  40058e:	90                   	nop
  40058f:	90                   	nop

0000000000400590 <__do_global_dtors_aux>:
  400590:	55                   	push   %rbp
  400591:	48 89 e5             	mov    %rsp,%rbp
  400594:	53                   	push   %rbx
  400595:	48 83 ec 08          	sub    $0x8,%rsp
  400599:	80 3d 90 0c 20 00 00 	cmpb   $0x0,0x200c90(%rip)        # 601230 <completed.6341>
  4005a0:	75 4b                	jne    4005ed <__do_global_dtors_aux+0x5d>
  4005a2:	bb 18 10 60 00       	mov    $0x601018,%ebx
  4005a7:	48 8b 05 8a 0c 20 00 	mov    0x200c8a(%rip),%rax        # 601238 <dtor_idx.6343>
  4005ae:	48 81 eb 10 10 60 00 	sub    $0x601010,%rbx
  4005b5:	48 c1 fb 03          	sar    $0x3,%rbx
  4005b9:	48 83 eb 01          	sub    $0x1,%rbx
  4005bd:	48 39 d8             	cmp    %rbx,%rax
  4005c0:	73 24                	jae    4005e6 <__do_global_dtors_aux+0x56>
  4005c2:	66 0f 1f 44 00 00    	nopw   0x0(%rax,%rax,1)
  4005c8:	48 83 c0 01          	add    $0x1,%rax
  4005cc:	48 89 05 65 0c 20 00 	mov    %rax,0x200c65(%rip)        # 601238 <dtor_idx.6343>
  4005d3:	ff 14 c5 10 10 60 00 	callq  *0x601010(,%rax,8)
  4005da:	48 8b 05 57 0c 20 00 	mov    0x200c57(%rip),%rax        # 601238 <dtor_idx.6343>
  4005e1:	48 39 d8             	cmp    %rbx,%rax
  4005e4:	72 e2                	jb     4005c8 <__do_global_dtors_aux+0x38>
  4005e6:	c6 05 43 0c 20 00 01 	movb   $0x1,0x200c43(%rip)        # 601230 <completed.6341>
  4005ed:	48 83 c4 08          	add    $0x8,%rsp
  4005f1:	5b                   	pop    %rbx
  4005f2:	c9                   	leaveq 
  4005f3:	c3                   	retq   
  4005f4:	66 66 66 2e 0f 1f 84 	nopw   %cs:0x0(%rax,%rax,1)
  4005fb:	00 00 00 00 00 

0000000000400600 <frame_dummy>:
  400600:	55                   	push   %rbp
  400601:	48 83 3d 17 0a 20 00 	cmpq   $0x0,0x200a17(%rip)        # 601020 <__JCR_END__>
  400608:	00 
  400609:	48 89 e5             	mov    %rsp,%rbp
  40060c:	74 12                	je     400620 <frame_dummy+0x20>
  40060e:	b8 00 00 00 00       	mov    $0x0,%eax
  400613:	48 85 c0             	test   %rax,%rax
  400616:	74 08                	je     400620 <frame_dummy+0x20>
  400618:	bf 20 10 60 00       	mov    $0x601020,%edi
  40061d:	c9                   	leaveq 
  40061e:	ff e0                	jmpq   *%rax
  400620:	c9                   	leaveq 
  400621:	c3                   	retq   
  400622:	90                   	nop
  400623:	90                   	nop
  400624:	90                   	nop
  400625:	90                   	nop
  400626:	90                   	nop
  400627:	90                   	nop
  400628:	90                   	nop
  400629:	90                   	nop
  40062a:	90                   	nop
  40062b:	90                   	nop
  40062c:	90                   	nop
  40062d:	90                   	nop
  40062e:	90                   	nop
  40062f:	90                   	nop

0000000000400630 <load>:
  400630:	53                   	push   %rbx
  400631:	41 89 d0             	mov    %edx,%r8d
  400634:	0f 31                	rdtsc  
  400636:	c1 ee 03             	shr    $0x3,%esi
  400639:	49 89 d2             	mov    %rdx,%r10
  40063c:	89 c0                	mov    %eax,%eax
  40063e:	89 f6                	mov    %esi,%esi
  400640:	49 c1 e2 20          	shl    $0x20,%r10
  400644:	49 89 fb             	mov    %rdi,%r11
  400647:	4c 8d 0c f7          	lea    (%rdi,%rsi,8),%r9
  40064b:	49 09 c2             	or     %rax,%r10
  40064e:	49 f7 d3             	not    %r11
  400651:	0f b6 05 d0 0b 20 00 	movzbl 0x200bd0(%rip),%eax        # 601228 <not_interrupted>
  400658:	66 0f 57 c0          	xorpd  %xmm0,%xmm0
  40065c:	4f 8d 1c 19          	lea    (%r9,%r11,1),%r11
  400660:	45 89 c0             	mov    %r8d,%r8d
  400663:	49 c1 eb 0c          	shr    $0xc,%r11
  400667:	66 0f 1f 84 00 00 00 	nopw   0x0(%rax,%rax,1)
  40066e:	00 00 
  400670:	84 c0                	test   %al,%al
  400672:	0f 84 d0 00 00 00    	je     400748 <load+0x118>
  400678:	4c 39 cf             	cmp    %r9,%rdi
  40067b:	73 f3                	jae    400670 <load+0x40>
  40067d:	48 8b 19             	mov    (%rcx),%rbx
  400680:	48 89 fe             	mov    %rdi,%rsi
  400683:	f2 0f 58 06          	addsd  (%rsi),%xmm0
  400687:	b8 18 00 00 00       	mov    $0x18,%eax
  40068c:	f2 0f 58 46 08       	addsd  0x8(%rsi),%xmm0
  400691:	f2 0f 58 46 10       	addsd  0x10(%rsi),%xmm0
  400696:	f2 0f 58 04 06       	addsd  (%rsi,%rax,1),%xmm0
  40069b:	48 83 c0 08          	add    $0x8,%rax
  40069f:	f2 0f 58 04 06       	addsd  (%rsi,%rax,1),%xmm0
  4006a4:	48 83 c0 08          	add    $0x8,%rax
  4006a8:	f2 0f 58 04 06       	addsd  (%rsi,%rax,1),%xmm0
  4006ad:	48 83 c0 08          	add    $0x8,%rax
  4006b1:	f2 0f 58 04 06       	addsd  (%rsi,%rax,1),%xmm0
  4006b6:	48 83 c0 08          	add    $0x8,%rax
  4006ba:	f2 0f 58 04 06       	addsd  (%rsi,%rax,1),%xmm0
  4006bf:	48 83 c0 08          	add    $0x8,%rax
  4006c3:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
  4006c8:	f2 0f 58 04 06       	addsd  (%rsi,%rax,1),%xmm0
  4006cd:	f2 0f 58 44 06 08    	addsd  0x8(%rsi,%rax,1),%xmm0
  4006d3:	f2 0f 58 44 06 10    	addsd  0x10(%rsi,%rax,1),%xmm0
  4006d9:	f2 0f 58 44 06 18    	addsd  0x18(%rsi,%rax,1),%xmm0
  4006df:	f2 0f 58 44 06 20    	addsd  0x20(%rsi,%rax,1),%xmm0
  4006e5:	f2 0f 58 44 06 28    	addsd  0x28(%rsi,%rax,1),%xmm0
  4006eb:	f2 0f 58 44 06 30    	addsd  0x30(%rsi,%rax,1),%xmm0
  4006f1:	f2 0f 58 44 06 38    	addsd  0x38(%rsi,%rax,1),%xmm0
  4006f7:	48 83 c0 40          	add    $0x40,%rax
  4006fb:	48 3d 00 10 00 00    	cmp    $0x1000,%rax
  400701:	75 c5                	jne    4006c8 <load+0x98>
  400703:	48 81 c6 00 10 00 00 	add    $0x1000,%rsi
  40070a:	0f 31                	rdtsc  
  40070c:	48 c1 e2 20          	shl    $0x20,%rdx
  400710:	89 c0                	mov    %eax,%eax
  400712:	48 09 c2             	or     %rax,%rdx
  400715:	48 89 d0             	mov    %rdx,%rax
  400718:	4c 29 d0             	sub    %r10,%rax
  40071b:	4c 39 c0             	cmp    %r8,%rax
  40071e:	72 ea                	jb     40070a <load+0xda>
  400720:	49 39 f1             	cmp    %rsi,%r9
  400723:	49 89 d2             	mov    %rdx,%r10
  400726:	0f 87 57 ff ff ff    	ja     400683 <load+0x53>
  40072c:	4a 8d 74 1b 01       	lea    0x1(%rbx,%r11,1),%rsi
  400731:	48 89 31             	mov    %rsi,(%rcx)
  400734:	0f b6 05 ed 0a 20 00 	movzbl 0x200aed(%rip),%eax        # 601228 <not_interrupted>
  40073b:	84 c0                	test   %al,%al
  40073d:	0f 85 35 ff ff ff    	jne    400678 <load+0x48>
  400743:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
  400748:	f2 48 0f 2c c0       	cvttsd2si %xmm0,%rax
  40074d:	5b                   	pop    %rbx
  40074e:	c3                   	retq   
  40074f:	90                   	nop

0000000000400750 <handler>:
  400750:	c6 05 d1 0a 20 00 00 	movb   $0x0,0x200ad1(%rip)        # 601228 <not_interrupted>
  400757:	c3                   	retq   
  400758:	0f 1f 84 00 00 00 00 	nopl   0x0(%rax,%rax,1)
  40075f:	00 

0000000000400760 <main>:
  400760:	48 89 6c 24 d8       	mov    %rbp,-0x28(%rsp)
  400765:	4c 89 6c 24 e8       	mov    %r13,-0x18(%rsp)
  40076a:	89 fd                	mov    %edi,%ebp
  40076c:	48 89 5c 24 d0       	mov    %rbx,-0x30(%rsp)
  400771:	4c 89 64 24 e0       	mov    %r12,-0x20(%rsp)
  400776:	49 89 f5             	mov    %rsi,%r13
  400779:	4c 89 74 24 f0       	mov    %r14,-0x10(%rsp)
  40077e:	4c 89 7c 24 f8       	mov    %r15,-0x8(%rsp)
  400783:	48 83 ec 48          	sub    $0x48,%rsp
  400787:	83 ff 01             	cmp    $0x1,%edi
  40078a:	48 c7 44 24 08 00 00 	movq   $0x0,0x8(%rsp)
  400791:	00 00 
  400793:	0f 8e 27 02 00 00    	jle    4009c0 <main+0x260>
  400799:	48 8b 7e 08          	mov    0x8(%rsi),%rdi
  40079d:	ba 0a 00 00 00       	mov    $0xa,%edx
  4007a2:	31 f6                	xor    %esi,%esi
  4007a4:	e8 6f fd ff ff       	callq  400518 <strtol@plt>
  4007a9:	85 c0                	test   %eax,%eax
  4007ab:	89 c3                	mov    %eax,%ebx
  4007ad:	0f 84 ed 01 00 00    	je     4009a0 <main+0x240>
  4007b3:	83 fd 02             	cmp    $0x2,%ebp
  4007b6:	0f 85 44 01 00 00    	jne    400900 <main+0x1a0>
  4007bc:	41 be 00 e1 f5 05    	mov    $0x5f5e100,%r14d
  4007c2:	41 bc 00 e1 f5 05    	mov    $0x5f5e100,%r12d
  4007c8:	41 bd 88 a6 26 00    	mov    $0x26a688,%r13d
  4007ce:	4c 89 f7             	mov    %r14,%rdi
  4007d1:	e8 22 fd ff ff       	callq  4004f8 <malloc@plt>
  4007d6:	48 85 c0             	test   %rax,%rax
  4007d9:	48 89 c5             	mov    %rax,%rbp
  4007dc:	0f 84 f7 01 00 00    	je     4009d9 <main+0x279>
  4007e2:	4c 89 f2             	mov    %r14,%rdx
  4007e5:	31 f6                	xor    %esi,%esi
  4007e7:	48 89 c7             	mov    %rax,%rdi
  4007ea:	e8 f9 fc ff ff       	callq  4004e8 <memset@plt>
  4007ef:	be 50 07 40 00       	mov    $0x400750,%esi
  4007f4:	bf 02 00 00 00       	mov    $0x2,%edi
  4007f9:	e8 2a fd ff ff       	callq  400528 <signal@plt>
  4007fe:	44 89 e1             	mov    %r12d,%ecx
  400801:	89 da                	mov    %ebx,%edx
  400803:	be 00 10 00 00       	mov    $0x1000,%esi
  400808:	bf 08 0c 40 00       	mov    $0x400c08,%edi
  40080d:	31 c0                	xor    %eax,%eax
  40080f:	e8 c4 fc ff ff       	callq  4004d8 <printf@plt>
  400814:	0f 31                	rdtsc  
  400816:	48 8d 4c 24 08       	lea    0x8(%rsp),%rcx
  40081b:	41 89 d6             	mov    %edx,%r14d
  40081e:	45 31 c0             	xor    %r8d,%r8d
  400821:	89 da                	mov    %ebx,%edx
  400823:	44 89 e6             	mov    %r12d,%esi
  400826:	48 89 ef             	mov    %rbp,%rdi
  400829:	41 89 c7             	mov    %eax,%r15d
  40082c:	e8 ff fd ff ff       	callq  400630 <load>
  400831:	0f 31                	rdtsc  
  400833:	48 89 d3             	mov    %rdx,%rbx
  400836:	89 c1                	mov    %eax,%ecx
  400838:	49 c1 e6 20          	shl    $0x20,%r14
  40083c:	48 c1 e3 20          	shl    $0x20,%rbx
  400840:	45 89 ff             	mov    %r15d,%r15d
  400843:	31 d2                	xor    %edx,%edx
  400845:	48 09 cb             	or     %rcx,%rbx
  400848:	4d 09 fe             	or     %r15,%r14
  40084b:	be 00 10 00 00       	mov    $0x1000,%esi
  400850:	4c 29 f3             	sub    %r14,%rbx
  400853:	bf 68 0c 40 00       	mov    $0x400c68,%edi
  400858:	45 89 ed             	mov    %r13d,%r13d
  40085b:	48 89 d8             	mov    %rbx,%rax
  40085e:	48 f7 74 24 08       	divq   0x8(%rsp)
  400863:	48 89 c3             	mov    %rax,%rbx
  400866:	48 89 c2             	mov    %rax,%rdx
  400869:	31 c0                	xor    %eax,%eax
  40086b:	e8 68 fc ff ff       	callq  4004d8 <printf@plt>
  400870:	48 85 db             	test   %rbx,%rbx
  400873:	f2 49 0f 2a c5       	cvtsi2sd %r13,%xmm0
  400878:	0f 88 e2 00 00 00    	js     400960 <main+0x200>
  40087e:	f2 48 0f 2a cb       	cvtsi2sd %rbx,%xmm1
  400883:	f2 0f 5e c1          	divsd  %xmm1,%xmm0
  400887:	f2 0f 10 0d 41 04 00 	movsd  0x441(%rip),%xmm1        # 400cd0 <_IO_stdin_used+0x1e8>
  40088e:	00 
  40088f:	f2 0f 59 05 29 04 00 	mulsd  0x429(%rip),%xmm0        # 400cc0 <_IO_stdin_used+0x1d8>
  400896:	00 
  400897:	f2 0f 59 05 29 04 00 	mulsd  0x429(%rip),%xmm0        # 400cc8 <_IO_stdin_used+0x1e0>
  40089e:	00 
  40089f:	66 0f 2e c1          	ucomisd %xmm1,%xmm0
  4008a3:	73 3b                	jae    4008e0 <main+0x180>
  4008a5:	f2 48 0f 2c f0       	cvttsd2si %xmm0,%rsi
  4008aa:	bf a0 0c 40 00       	mov    $0x400ca0,%edi
  4008af:	31 c0                	xor    %eax,%eax
  4008b1:	e8 22 fc ff ff       	callq  4004d8 <printf@plt>
  4008b6:	31 c0                	xor    %eax,%eax
  4008b8:	48 8b 5c 24 18       	mov    0x18(%rsp),%rbx
  4008bd:	48 8b 6c 24 20       	mov    0x20(%rsp),%rbp
  4008c2:	4c 8b 64 24 28       	mov    0x28(%rsp),%r12
  4008c7:	4c 8b 6c 24 30       	mov    0x30(%rsp),%r13
  4008cc:	4c 8b 74 24 38       	mov    0x38(%rsp),%r14
  4008d1:	4c 8b 7c 24 40       	mov    0x40(%rsp),%r15
  4008d6:	48 83 c4 48          	add    $0x48,%rsp
  4008da:	c3                   	retq   
  4008db:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
  4008e0:	f2 0f 5c c1          	subsd  %xmm1,%xmm0
  4008e4:	48 b8 00 00 00 00 00 	mov    $0x8000000000000000,%rax
  4008eb:	00 00 80 
  4008ee:	f2 48 0f 2c f0       	cvttsd2si %xmm0,%rsi
  4008f3:	48 31 c6             	xor    %rax,%rsi
  4008f6:	eb b2                	jmp    4008aa <main+0x14a>
  4008f8:	0f 1f 84 00 00 00 00 	nopl   0x0(%rax,%rax,1)
  4008ff:	00 
  400900:	49 8b 7d 10          	mov    0x10(%r13),%rdi
  400904:	31 f6                	xor    %esi,%esi
  400906:	ba 0a 00 00 00       	mov    $0xa,%edx
  40090b:	e8 08 fc ff ff       	callq  400518 <strtol@plt>
  400910:	85 c0                	test   %eax,%eax
  400912:	41 89 c4             	mov    %eax,%r12d
  400915:	74 69                	je     400980 <main+0x220>
  400917:	a9 ff 0f 00 00       	test   $0xfff,%eax
  40091c:	75 62                	jne    400980 <main+0x220>
  40091e:	89 c6                	mov    %eax,%esi
  400920:	bf 09 0b 40 00       	mov    $0x400b09,%edi
  400925:	31 c0                	xor    %eax,%eax
  400927:	e8 ac fb ff ff       	callq  4004d8 <printf@plt>
  40092c:	83 fd 03             	cmp    $0x3,%ebp
  40092f:	0f 84 bd 00 00 00    	je     4009f2 <main+0x292>
  400935:	49 8b 7d 18          	mov    0x18(%r13),%rdi
  400939:	ba 0a 00 00 00       	mov    $0xa,%edx
  40093e:	31 f6                	xor    %esi,%esi
  400940:	45 89 e6             	mov    %r12d,%r14d
  400943:	e8 d0 fb ff ff       	callq  400518 <strtol@plt>
  400948:	bf b0 0b 40 00       	mov    $0x400bb0,%edi
  40094d:	89 c6                	mov    %eax,%esi
  40094f:	41 89 c5             	mov    %eax,%r13d
  400952:	31 c0                	xor    %eax,%eax
  400954:	e8 7f fb ff ff       	callq  4004d8 <printf@plt>
  400959:	e9 70 fe ff ff       	jmpq   4007ce <main+0x6e>
  40095e:	66 90                	xchg   %ax,%ax
  400960:	48 89 d8             	mov    %rbx,%rax
  400963:	83 e3 01             	and    $0x1,%ebx
  400966:	48 d1 e8             	shr    %rax
  400969:	48 09 d8             	or     %rbx,%rax
  40096c:	f2 48 0f 2a c8       	cvtsi2sd %rax,%xmm1
  400971:	f2 0f 58 c9          	addsd  %xmm1,%xmm1
  400975:	e9 09 ff ff ff       	jmpq   400883 <main+0x123>
  40097a:	66 0f 1f 44 00 00    	nopw   0x0(%rax,%rax,1)
  400980:	44 89 e2             	mov    %r12d,%edx
  400983:	be 00 10 00 00       	mov    $0x1000,%esi
  400988:	bf 60 0b 40 00       	mov    $0x400b60,%edi
  40098d:	31 c0                	xor    %eax,%eax
  40098f:	e8 44 fb ff ff       	callq  4004d8 <printf@plt>
  400994:	b8 ff ff ff ff       	mov    $0xffffffff,%eax
  400999:	e9 1a ff ff ff       	jmpq   4008b8 <main+0x158>
  40099e:	66 90                	xchg   %ax,%ax
  4009a0:	31 f6                	xor    %esi,%esi
  4009a2:	bf 28 0b 40 00       	mov    $0x400b28,%edi
  4009a7:	31 c0                	xor    %eax,%eax
  4009a9:	e8 2a fb ff ff       	callq  4004d8 <printf@plt>
  4009ae:	b8 ff ff ff ff       	mov    $0xffffffff,%eax
  4009b3:	e9 00 ff ff ff       	jmpq   4008b8 <main+0x158>
  4009b8:	0f 1f 84 00 00 00 00 	nopl   0x0(%rax,%rax,1)
  4009bf:	00 
  4009c0:	48 8b 36             	mov    (%rsi),%rsi
  4009c3:	bf ec 0a 40 00       	mov    $0x400aec,%edi
  4009c8:	31 c0                	xor    %eax,%eax
  4009ca:	e8 09 fb ff ff       	callq  4004d8 <printf@plt>
  4009cf:	b8 ff ff ff ff       	mov    $0xffffffff,%eax
  4009d4:	e9 df fe ff ff       	jmpq   4008b8 <main+0x158>
  4009d9:	44 89 e6             	mov    %r12d,%esi
  4009dc:	bf d8 0b 40 00       	mov    $0x400bd8,%edi
  4009e1:	31 c0                	xor    %eax,%eax
  4009e3:	e8 f0 fa ff ff       	callq  4004d8 <printf@plt>
  4009e8:	b8 ff ff ff ff       	mov    $0xffffffff,%eax
  4009ed:	e9 c6 fe ff ff       	jmpq   4008b8 <main+0x158>
  4009f2:	45 89 e6             	mov    %r12d,%r14d
  4009f5:	41 bd 88 a6 26 00    	mov    $0x26a688,%r13d
  4009fb:	e9 ce fd ff ff       	jmpq   4007ce <main+0x6e>

0000000000400a00 <__libc_csu_fini>:
  400a00:	f3 c3                	repz retq 
  400a02:	66 66 66 66 66 2e 0f 	nopw   %cs:0x0(%rax,%rax,1)
  400a09:	1f 84 00 00 00 00 00 

0000000000400a10 <__libc_csu_init>:
  400a10:	48 89 6c 24 d8       	mov    %rbp,-0x28(%rsp)
  400a15:	4c 89 64 24 e0       	mov    %r12,-0x20(%rsp)
  400a1a:	48 8d 2d df 05 20 00 	lea    0x2005df(%rip),%rbp        # 601000 <__CTOR_LIST__>
  400a21:	4c 8d 25 d8 05 20 00 	lea    0x2005d8(%rip),%r12        # 601000 <__CTOR_LIST__>
  400a28:	4c 89 6c 24 e8       	mov    %r13,-0x18(%rsp)
  400a2d:	4c 89 74 24 f0       	mov    %r14,-0x10(%rsp)
  400a32:	4c 89 7c 24 f8       	mov    %r15,-0x8(%rsp)
  400a37:	48 89 5c 24 d0       	mov    %rbx,-0x30(%rsp)
  400a3c:	48 83 ec 38          	sub    $0x38,%rsp
  400a40:	4c 29 e5             	sub    %r12,%rbp
  400a43:	41 89 fd             	mov    %edi,%r13d
  400a46:	49 89 f6             	mov    %rsi,%r14
  400a49:	48 c1 fd 03          	sar    $0x3,%rbp
  400a4d:	49 89 d7             	mov    %rdx,%r15
  400a50:	e8 5b fa ff ff       	callq  4004b0 <_init>
  400a55:	48 85 ed             	test   %rbp,%rbp
  400a58:	74 1c                	je     400a76 <__libc_csu_init+0x66>
  400a5a:	31 db                	xor    %ebx,%ebx
  400a5c:	0f 1f 40 00          	nopl   0x0(%rax)
  400a60:	4c 89 fa             	mov    %r15,%rdx
  400a63:	4c 89 f6             	mov    %r14,%rsi
  400a66:	44 89 ef             	mov    %r13d,%edi
  400a69:	41 ff 14 dc          	callq  *(%r12,%rbx,8)
  400a6d:	48 83 c3 01          	add    $0x1,%rbx
  400a71:	48 39 eb             	cmp    %rbp,%rbx
  400a74:	72 ea                	jb     400a60 <__libc_csu_init+0x50>
  400a76:	48 8b 5c 24 08       	mov    0x8(%rsp),%rbx
  400a7b:	48 8b 6c 24 10       	mov    0x10(%rsp),%rbp
  400a80:	4c 8b 64 24 18       	mov    0x18(%rsp),%r12
  400a85:	4c 8b 6c 24 20       	mov    0x20(%rsp),%r13
  400a8a:	4c 8b 74 24 28       	mov    0x28(%rsp),%r14
  400a8f:	4c 8b 7c 24 30       	mov    0x30(%rsp),%r15
  400a94:	48 83 c4 38          	add    $0x38,%rsp
  400a98:	c3                   	retq   
  400a99:	90                   	nop
  400a9a:	90                   	nop
  400a9b:	90                   	nop
  400a9c:	90                   	nop
  400a9d:	90                   	nop
  400a9e:	90                   	nop
  400a9f:	90                   	nop

0000000000400aa0 <__do_global_ctors_aux>:
  400aa0:	55                   	push   %rbp
  400aa1:	48 89 e5             	mov    %rsp,%rbp
  400aa4:	53                   	push   %rbx
  400aa5:	48 83 ec 08          	sub    $0x8,%rsp
  400aa9:	48 8b 05 50 05 20 00 	mov    0x200550(%rip),%rax        # 601000 <__CTOR_LIST__>
  400ab0:	48 83 f8 ff          	cmp    $0xffffffffffffffff,%rax
  400ab4:	74 19                	je     400acf <__do_global_ctors_aux+0x2f>
  400ab6:	bb 00 10 60 00       	mov    $0x601000,%ebx
  400abb:	0f 1f 44 00 00       	nopl   0x0(%rax,%rax,1)
  400ac0:	48 83 eb 08          	sub    $0x8,%rbx
  400ac4:	ff d0                	callq  *%rax
  400ac6:	48 8b 03             	mov    (%rbx),%rax
  400ac9:	48 83 f8 ff          	cmp    $0xffffffffffffffff,%rax
  400acd:	75 f1                	jne    400ac0 <__do_global_ctors_aux+0x20>
  400acf:	48 83 c4 08          	add    $0x8,%rsp
  400ad3:	5b                   	pop    %rbx
  400ad4:	c9                   	leaveq 
  400ad5:	c3                   	retq   
  400ad6:	90                   	nop
  400ad7:	90                   	nop

Disassembly of section .fini:

0000000000400ad8 <_fini>:
  400ad8:	48 83 ec 08          	sub    $0x8,%rsp
  400adc:	e8 af fa ff ff       	callq  400590 <__do_global_dtors_aux>
  400ae1:	48 83 c4 08          	add    $0x8,%rsp
  400ae5:	c3                   	retq   
