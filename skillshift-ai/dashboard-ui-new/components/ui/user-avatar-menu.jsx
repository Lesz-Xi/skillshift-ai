"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Settings,
  Bug,
  HelpCircle,
  Share2,
  Crown,
  LogOut,
  User,
  Upload,
  Camera,
} from "lucide-react";
import { toast } from "sonner";

const UserAvatarMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [avatar, setAvatar] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  // Default avatar if no custom avatar is set
  const defaultAvatar = (
    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-amber-200 to-amber-100 flex items-center justify-center text-neutral-900 font-semibold text-sm">
      U
    </div>
  );

  const handleAvatarClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      toast.error("Please select an image file");
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("Image size must be less than 5MB");
      return;
    }

    setIsUploading(true);

    try {
      // Simulate upload process
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setAvatar(previewUrl);

      toast.success("Avatar updated successfully!");
    } catch (error) {
      toast.error("Failed to upload avatar. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const menuItems = [
    {
      icon: Camera,
      label: "Change Avatar",
      action: () => {
        handleAvatarClick();
        setIsOpen(false);
      },
    },
    {
      icon: Settings,
      label: "Settings",
      action: () => {
        toast.info("Settings panel coming soon!");
        setIsOpen(false);
      },
    },
    {
      icon: Bug,
      label: "Report Issue",
      action: () => {
        toast.info("Issue reporting feature coming soon!");
        setIsOpen(false);
      },
    },
    {
      icon: HelpCircle,
      label: "Help & Support",
      action: () => {
        toast.info("Help center coming soon!");
        setIsOpen(false);
      },
    },
    {
      icon: Share2,
      label: "Share Profile",
      action: () => {
        toast.info("Profile sharing feature coming soon!");
        setIsOpen(false);
      },
    },
    {
      icon: Crown,
      label: "Upgrade Plan",
      action: () => {
        toast.info("Upgrade options coming soon!");
        setIsOpen(false);
      },
    },
  ];

  const menuVariants = {
    hidden: {
      opacity: 0,
      scale: 0.95,
      y: 10,
      transition: { duration: 0.15 },
    },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: {
        duration: 0.2,
        ease: "easeOut",
        staggerChildren: 0.05,
      },
    },
    exit: {
      opacity: 0,
      scale: 0.95,
      y: 10,
      transition: { duration: 0.15 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.2, ease: "easeOut" },
    },
  };

  return (
    <div className="relative">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileUpload}
        className="hidden"
      />

      {/* Single Avatar with Dropdown Menu */}
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="relative"
          >
            <Button
              variant="ghost"
              size="sm"
              disabled={isUploading}
              className="w-12 h-12 p-0 rounded-full bg-neutral-800 hover:bg-neutral-700 border border-neutral-600 hover:border-amber-300 transition-all duration-200"
            >
              {isUploading ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-6 h-6 border-2 border-amber-300 border-t-transparent rounded-full"
                />
              ) : avatar ? (
                <img
                  src={avatar}
                  alt="User Avatar"
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                defaultAvatar
              )}
            </Button>

            {/* Upload indicator */}
            {isUploading && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="absolute -top-1 -right-1 w-4 h-4 bg-amber-300 rounded-full flex items-center justify-center"
              >
                <Upload className="w-2.5 h-2.5 text-neutral-900" />
              </motion.div>
            )}
          </motion.div>
        </DropdownMenuTrigger>

        <DropdownMenuContent
          align="end"
          className="w-56 bg-neutral-900 border-neutral-700 shadow-2xl"
          side="top"
          sideOffset={8}
        >
          <AnimatePresence>
            {isOpen && (
              <motion.div
                variants={menuVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="py-2"
              >
                {/* User Info */}
                <motion.div
                  variants={itemVariants}
                  className="px-3 py-2 border-b border-neutral-700"
                >
                  <div className="flex items-center space-x-3">
                    {avatar ? (
                      <img
                        src={avatar}
                        alt="User Avatar"
                        className="w-8 h-8 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-200 to-amber-100 flex items-center justify-center text-neutral-900 font-semibold text-xs">
                        U
                      </div>
                    )}
                    <div>
                      <p className="text-sm font-medium text-white">
                        MLBB Player
                      </p>
                      <p className="text-xs text-neutral-400">
                        SkillShift AI User
                      </p>
                    </div>
                  </div>
                </motion.div>

                {/* Menu Items */}
                {menuItems.map((item, index) => (
                  <motion.div key={item.label} variants={itemVariants}>
                    <DropdownMenuItem
                      onClick={item.action}
                      className="flex items-center space-x-3 px-3 py-2 text-sm text-neutral-300 hover:text-white hover:bg-neutral-800 cursor-pointer transition-colors"
                    >
                      <item.icon className="w-4 h-4" />
                      <span>{item.label}</span>
                    </DropdownMenuItem>
                  </motion.div>
                ))}

                <DropdownMenuSeparator className="bg-neutral-700" />

                {/* Sign Out */}
                <motion.div variants={itemVariants}>
                  <DropdownMenuItem
                    onClick={() => {
                      toast.info("Sign out feature coming soon!");
                      setIsOpen(false);
                    }}
                    className="flex items-center space-x-3 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-900/20 cursor-pointer transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </DropdownMenuItem>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default UserAvatarMenu;
